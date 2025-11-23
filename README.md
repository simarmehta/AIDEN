# AIDEN - Your RAG Assistant

AIDEN is an advanced **Retrieval-Augmented Generation (RAG)** application designed to streamline the process of ingesting, querying, and managing knowledge from diverse documentation sources.

## Table of Contents
1. [Features](#features)
2. [Directory Structure](#directory-structure)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [How It Works](#how-it-works)
---

## Features

- **Multi-Vendor Registration**: Easily register multiple knowledge vendors with metadata including name, domain, and detailed descriptions.
- **Incremental Ingestion**: Append new documents or links.
- **Advanced Chunking**: Supports sentence-based, paragraph-based chunking methods.
- **Efficient Embedding**: Generate semantic embeddings for accurate retrieval.
- **Interactive Chat Interface**: A user-friendly chat UI.

---

## Directory Structure

```
aiden/
├── main.py                      # FastAPI server and API endpoints
├── query_router.py              # LLM-based vendor selection logic
├── db.py                        # Database operations (connections, queries)
├── single_vendor_ingest.py      # Document ingestion per vendor
├── embeddings.py                # Embedding generation utilities
├── chunkdigest.py               # Advanced chunking pipeline
├── create_table.py              # Database schema creation and migration
|── index.html                   # Chat interface
├── home.html                    # Landing page
|── vendor_registration.html     # Vendor management UI
├── utils.py                     # Text extraction and cleaning utilities
├── requirements.txt             # Python dependencies
```

---

## Requirements

- **Python**: >=3.10
- **PostgreSQL** with `pgvector` extension
- **OpenAI API Key**


---

## Installation

**Step 1: Clone the Repository**
```bash
git clone https://github.com/yourusername/aiden-rag.git
cd aiden
```

**Step 2: Setup Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Step 3: Configure Environment Variables**
Create a `.env` file:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=youruser
DB_PASSWORD=yourpassword
DB_NAME=yourdb
OPENAI_API_KEY=your-api-key
```

**Step 4: Initialize Database**
Ensure PostgreSQL has the `pgvector` extension enabled:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
Then run:
```bash
python create_table.py
```

---

## Usage

**Run the FastAPI Application**:
```bash
uvicorn main:app --reload
```

**Access via Browser**:
- **Homepage**: `http://127.0.0.1:8000`
- **Chat UI**: `http://127.0.0.1:8000/chat`
- **Vendor Registration UI**: `http://127.0.0.1:8000/vendor_registration`

**Register New Vendor**:
- Navigate to the vendor registration page, input details (name, description, URLs).
- Submit to trigger automatic ingestion and embedding.

**Append New Links**:
- Update existing vendors with additional links directly from the UI or through dedicated API endpoints.

**Query Documentation**:
- Enter questions via the Chat UI.
- Optionally specify a vendor for targeted queries.

---

## How It Works

**Ingestion Pipeline**:
- Fetch documents from URLs (HTML/PDF).
- Clean and chunk text (sentence/paragraph/token-level).
- Generate embeddings and store them in PostgreSQL (`pgvector`).

**Query Process**:
- Accept user queries through UI.
- Determine the relevant vendor using LLM-based router if unspecified.
- Retrieve semantically similar chunks using vector similarity search.
- Pass context to OpenAI GPT-4 to generate precise answers.
