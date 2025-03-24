
import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            dbname=os.getenv("DB_NAME")
        )
        print("Database connection successful!")
        return conn
    except Exception as e:
        print(" Error connecting to the database:", e)
        raise

def insert_documents(documents):
    
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    INSERT INTO rag_db (vendor, domain, type, section, content, url, embedding)
    VALUES %s
    """
    execute_values(cur, sql, documents)

    conn.commit()
    cur.close()
    conn.close()
    print(f" Inserted {len(documents)} records into 'rag_db'.")

def insert_vendor(vendor_name, domain, source_type, source_urls, chunk_strategy, is_private, description):
    conn = get_connection()
    cur = conn.cursor()

    sql = """
    INSERT INTO vendors (vendor_name, domain, source_type, source_urls, chunk_strategy, is_private, description)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id;
    """
    cur.execute(sql, (vendor_name, domain, source_type, source_urls, chunk_strategy, is_private, description))
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    print(f"New vendor '{vendor_name}' inserted with ID {new_id}.")
    return new_id

def get_all_vendors():
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, vendor_name, domain, source_type, source_urls, chunk_strategy, last_ingested FROM vendors;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
