> Terminology update: switched LAG to RAG.
# AIDEN - Your RAG Assistant
> Terminology update: switched RAG to RAG.






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
