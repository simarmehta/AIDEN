from typing import List
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

def llm_query_router(query: str, vendor_list: List[dict]):
    print("[DEBUG] Entering llm_query_router with query:", query)
    valid_vendors_str = json.dumps(vendor_list, indent=2)
    system_prompt = f"""
You are a smart query router. Based on the user query, decide which vendor(s) are most relevant.
You are given a list of vendors, each with a 'name' and a 'description'. Choose the most appropriate vendor(s) based on the meaning of the query.
{valid_vendors_str}

Respond with a JSON list of only the 'name' field of the vendors that match the query.
Eg: ["dev_docs"], or ["dev_docs", "ml_papers"].
Never return an empty list. If unsure, return the most likely vendors.
"""
    # system_prompt = f"""
    # You are a smart query router. Based on the user query, decide which vendor(s) are relevant.
    # Valid vendors: {valid_vendors_str}
    # Return only a JSON list, e.g. ["dev_docs"] or ["ml_papers", "dev_docs"].
    # If you're unsure, return all relevant vendors. Do not return an empty list.

    # """
    print("[DEBUG] All vendors:\n", valid_vendors_str)
    user_prompt = f"Query: {query}\nAnswer:"
    
    print("[DEBUG] System prompt for LLM:\n", system_prompt)
    print("[DEBUG] User prompt portion:\n", user_prompt)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )
        vendors_str = response.choices[0].message.content.strip()
        print("[DEBUG] Raw LLM router output:", vendors_str)
        vendors = json.loads(vendors_str)
        print("[DEBUG] Parsed vendor list from LLM:", vendors)
        if not isinstance(vendors, list) or not vendors:
            print("[DEBUG] LLM did not return a list, using fallback.")
            vendors = [v["name"] for v in vendor_list]
    except Exception as e:
        print("LLM routing error:", e)
        vendors = [v["name"] for v in vendor_list]
    print("[DEBUG] Final routed vendors:", vendors)
    return vendors
