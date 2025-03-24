from fastapi import BackgroundTasks, FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import openai

from embeddings import generate_embedding
from query_router import llm_query_router
from db import get_connection, insert_vendor
from single_vendor_ingest import ingest_only_new_links, ingest_single_vendor

load_dotenv()

app = FastAPI()

@app.get("/")
def serve_home():
    return FileResponse(os.path.join(os.path.dirname(__file__), "home.html"))

@app.get("/chat")
def serve_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

@app.get("/vendor_registration")
def serve_vendor_registration():
    return FileResponse(os.path.join(os.path.dirname(__file__), "vendor_registration.html"))

class VendorRegistration(BaseModel):
    vendor_name: str
    domain: str
    source_type: str 
    source_urls: List[str]
    chunk_strategy: Optional[str] = "sentence"
    is_private:bool=False
    description: Optional[str]=""

#   Allows a vendor to register and ingests data  
@app.post("/register_vendor")
def register_vendor_endpoint(
    reg_data: VendorRegistration,
    background_tasks: BackgroundTasks
):
    try:
        #insert
        new_id = insert_vendor(
            reg_data.vendor_name,
            reg_data.domain,
            reg_data.source_type,
            reg_data.source_urls,
            reg_data.chunk_strategy,
            reg_data.is_private,
            reg_data.description
        )

        # ingest
        background_tasks.add_task(
            ingest_single_vendor,
            new_id,                 
            reg_data.vendor_name,
            reg_data.domain,
            reg_data.source_type,
            reg_data.source_urls,
            reg_data.chunk_strategy
        )

        return {
            "message": "Vendor registered and ingestion started",
            "vendor_id": new_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
class VendorAppend(BaseModel):
    vendor_name: str
    new_links: List[str]

@app.put("/append_vendor_links")
def append_vendor_links(update: VendorAppend, background_tasks: BackgroundTasks):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, source_urls, domain, source_type, chunk_strategy
        FROM vendors
        WHERE vendor_name = %s
    """, (update.vendor_name,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor_id, old_urls, domain, source_type, chunk_strat = row
    old_urls = old_urls if old_urls else []

    combined_urls = list(set(old_urls + update.new_links))
    #new links
    new_unique_links = list(set(update.new_links) - set(old_urls))

    #update
    cur.execute("""
        UPDATE vendors
        SET source_urls = %s
        WHERE id = %s
    """, (combined_urls, vendor_id))
    conn.commit()
    cur.close()
    conn.close()

    # ingestion fo new links 
    if new_unique_links:
        background_tasks.add_task(
            ingest_only_new_links,
            vendor_id,
            update.vendor_name,
            domain,
            source_type,
            chunk_strat,
            new_unique_links
        )

    return {
        "message": f"Appended {len(new_unique_links)} new links to vendor '{update.vendor_name}'",
        "new_total_links": len(combined_urls)
    }

def get_all_vendors():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT vendor_name,description FROM vendors WHERE is_private = false;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    vendor_list = [{"name": row[0], "description": row[1]} for row in rows]
    return vendor_list


#RAG 
class RAGRequest(BaseModel):
    query: str
    top_k: int = 10
    vendor: str = None 


@app.post("/rag")
def generate_rag_answer(request: RAGRequest):
   
    query_vector = generate_embedding(request.query, is_query=True)
    conn = get_connection()
    cur = conn.cursor()

    if request.vendor:
        sql = """
        SELECT id, content, vendor, section, url, embedding <=> %s::vector AS distance
        FROM rag_db
        WHERE vendor = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
        """
        cur.execute(sql, (query_vector, request.vendor, query_vector, request.top_k))
        rows=cur.fetchall()
        routed_vendors = [request.vendor]
    else:

        all_vendors = get_all_vendors()  
        print("DEBUG: all vendors:", all_vendors)
        routed_vendors = llm_query_router(request.query, all_vendors)
        print("DEBUG: LLM chose vendors:", routed_vendors)

        rows = []
        if len(routed_vendors) == 1:
            #just one vendor
            cur.execute("""
                SELECT rag_db.id, rag_db.content, rag_db.vendor, rag_db.section, rag_db.url,
                       rag_db.embedding <=> %s::vector AS distance
                FROM rag_db
                JOIN vendors ON rag_db.vendor = vendors.vendor_name
                WHERE vendors.is_private = false
                  AND rag_db.vendor = %s
                ORDER BY rag_db.embedding <=> %s::vector
                LIMIT %s;
            """, (query_vector, routed_vendors[0], query_vector, request.top_k))
            rows = cur.fetchall()
        else:
            # many vendors routed
            per_vendor_k = max(1, request.top_k // len(routed_vendors))
            for vendor in routed_vendors:
                cur.execute("""
                    SELECT rag_db.id, rag_db.content, rag_db.vendor, rag_db.section, rag_db.url,
                           rag_db.embedding <=> %s::vector AS distance
                    FROM rag_db
                    JOIN vendors ON rag_db.vendor = vendors.vendor_name
                    WHERE vendors.is_private = false
                      AND rag_db.vendor = %s
                    ORDER BY rag_db.embedding <=> %s::vector
                    LIMIT %s;
                """, (query_vector, vendor, query_vector, per_vendor_k))
                rows.extend(cur.fetchall())

    cur.close()
    conn.close()

    retrieved_docs = [
        {
            "id": row[0],
            "content": row[1],
            "vendor": row[2],
            "section": row[3],
            "url": row[4],
            "distance": row[5]
        }
        for row in rows
    ]
    for doc in retrieved_docs:
        print(f"[DEBUG] Retrieved content:\n{doc['content']}\n---\n")


    context = "\n\n".join(f"[{doc['vendor']}] {doc['content']}" for doc in retrieved_docs)
    prompt = f"""
You are a helpful assistant with access to the following context.

- Use only the context to answer the user's question.
- If the context contains content from multiple sources, compare them clearly.
- If the answer requires info from multiple sections or vendors, use them all.
- At the end of your answer, mention the vendors or topics you used.
- If the answer is not found in the context, reply: "I'm sorry, but I don’t have information on that."

Context:
{context}
Question: {request.query}
Answer:
"""

    openai.api_key = os.getenv("OPENAI_API_KEY")

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only uses the provided context and gives an in detail answer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        answer = response.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "query": request.query,
        "routed_vendors": routed_vendors,
        "answer": answer,
        "retrieved_docs": retrieved_docs
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
