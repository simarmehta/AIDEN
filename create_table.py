from db import get_connection

def create_table():
    conn = get_connection()
    cur = conn.cursor()

    # Drop old rag_db table
    cur.execute("DROP TABLE IF EXISTS rag_db;")
    
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # rag_db table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rag_db (
            id SERIAL PRIMARY KEY,
            vendor TEXT,
            domain TEXT,
            type TEXT,
            section TEXT,
            content TEXT,
            url TEXT,
            embedding VECTOR(768)
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS rag_embedding_cosine_idx
        ON rag_db
        USING hnsw (embedding vector_cosine_ops);
    """)

    #  vendors TABLE
    cur.execute("DROP TABLE IF EXISTS vendors;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id SERIAL PRIMARY KEY,
            vendor_name TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            source_type TEXT NOT NULL,       
            source_urls TEXT[] NOT NULL,
            chunk_strategy TEXT DEFAULT 'sentence',
            last_ingested TIMESTAMP,
            is_private BOOLEAN DEFAULT false,
            description TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("'rag_db' and 'vendors' tables created successfuly")

if __name__ == "__main__":
    create_table()
