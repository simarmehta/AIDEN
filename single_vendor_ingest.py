# single_vendor_ingest.py
import os
import requests
import tempfile
from datetime import datetime
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup

import re

from db import get_connection, insert_documents
from embeddings import generate_embedding
from utils import fetch_html, extract_text_from_html, clean_text

def ingest_single_vendor(v_id, v_name, domain, source_type, source_urls, chunk_strat):
    print(f"Ingesting links for vendor '{v_name}'...")
    do_ingestion(v_id, v_name, domain, source_type, source_urls, chunk_strat)
    print(f"Done ingesting links for vendor '{v_name}'.")

def ingest_only_new_links(v_id, v_name, domain, source_type, chunk_strat, new_links):
    print(f"Ingesting only new links for vendor '{v_name}'...")
    do_ingestion(v_id, v_name, domain, source_type, new_links, chunk_strat)
    print(f"Done ingesting new links for vendor '{v_name}'.")

def do_ingestion(v_id, v_name, domain, source_type, urls, chunk_strat):
    conn = get_connection()
    cur = conn.cursor()

    for link in urls:
        print(f"Processing: {link}")
        raw_text = fetch_data(link, source_type)
        cleaned = clean_text(raw_text, mode=chunk_strat)
        if chunk_strat == "sentence":
            chunks = chunk_text_by_sentences(cleaned)
        elif chunk_strat == "paragraph":
            chunks = chunk_text_by_paragraphs(cleaned)
        else:
            chunks = [cleaned]
        print(f"Chunk strategy for '{link}': {chunk_strat}")
        print(f" Chunks generated from '{link}': {len(chunks)}")
        records = []
        for chunk in chunks:
            if len(chunk.strip()) < 50:
                continue
            emb = generate_embedding(chunk, is_query=False)
            records.append((v_name, domain, source_type, "auto_section", chunk, link, emb))
        if records:
            insert_documents(records)
    cur.execute("UPDATE vendors SET last_ingested = %s WHERE id = %s", (datetime.now(), v_id))
    conn.commit()
    cur.close()
    conn.close()

def fetch_data(src, source_type):
    if source_type == "web_scrape":
        html = fetch_html(src)
        if html:
            return extract_text_from_html(html)
        else:
            return ""
    elif source_type == "pdf_links":
        return parse_pdf(src)
    elif source_type == "plaintext":
        return src
    else:
        return ""
def parse_pdf(url):
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"PDF fetch error: {e}")
        return ""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(r.content)
        tmp.flush()
        tmp_path = tmp.name
    extracted_text = []
    try:
        reader = PdfReader(tmp_path)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            page_text = page_text.replace('\x00', '')
            extracted_text.append(page_text)
    except Exception as e:
        print(f"PDF parse error: {e}")
    try:
        os.remove(tmp_path)
    except:
        pass
    extracted = "\n".join(extracted_text)
    print(f"Extracted text length from PDF: {len(extracted)}")
    print(f"Preview:\n{extracted[:1000]}...\n")
    return extracted



def chunk_text_by_sentences(text, chunk_size=400, overlap_sentences=1):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    i = 0
    while i < len(sentences):
        current_chunk = sentences[i].strip()
        j = i + 1
        while j < len(sentences) and (len(current_chunk) + len(sentences[j]) + 1) <= chunk_size:
            current_chunk += " " + sentences[j].strip()
            j += 1
        chunks.append(current_chunk)
        i = max(j - overlap_sentences, i + 1)
    return chunks
def chunk_text_by_paragraphs(text, chunk_size=700):
    paragraphs = text.splitlines()
    print(f" Detected {len(paragraphs)} paragraphs before chunking.")
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 1 <= chunk_size:
            current_chunk += para + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = para + "\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks
