# Enterprise Retrieval-Augmented Generation (RAG) System

A production-grade, modular RAG application featuring decoupled **Document Ingestion** and **Chatbot Query** pipelines, local **Hugging Face** dense vector embeddings, persistent **ChromaDB** storage, **Gemini API** context-grounded reasoning, and a clean **Streamlit** web interface.

---

## Architecture Overview

```
                                  USER QUERY / UPLOAD
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           STREAMLIT USER INTERFACE                              │
│  • Multi-format Upload (PDF, DOCX, TXT)     • Chat History & Conversation State │
│  • Document Library & Deletion Management   • Expandable Source Citation Cards  │
└────────────────────────┬────────────────────────────────────────┬───────────────┘
                         │                                        │
                         ▼                                        ▼
┌──────────────────────────────────────────────┐ ┌────────────────────────────────┐
│              INGESTION PIPELINE              │ │        CHATBOT PIPELINE        │
│                                              │ │                                │
│ 1. Extraction (pypdf, python-docx, text)     │ │ 1. Query Embedding (Local HF)  │
│ 2. Deduplication (SHA-256 Content Hashing)   │ │ 2. Semantic Similarity Search  │
│ 3. Recursive Character Chunking              │ │ 3. Source Citation Formatting  │
│ 4. Embeddings (all-MiniLM-L6-v2 on MPS/CPU)  │ │ 4. Context-Grounded Prompting  │
│ 5. Metadata Enrichment (Source, Page, ID)    │ │ 5. Google Gemini API LLM       │
│                                              │ │ 6. Anti-Hallucination Guard    │
└──────────────────────┬───────────────────────┘ └────────────────┬───────────────┘
                       │                                          │
                       ▼                                          │
        ┌─────────────────────────────────────────────────────────┴─────────┐
        │                       CHROMADB VECTOR STORE                       │
        │  • Persistent disk storage at ./data/chroma_db                    │
        │  • Cosine & L2 index across restarts                              │
        │  • Document & chunk collection registry                           │
        └───────────────────────────────────────────────────────────────────┘
```

---

## Key Features

1. **Multi-Format Ingestion**:
   - **PDF**: Page-by-page text extraction with preservation of 1-based page numbers using `pypdf`.
   - **DOCX**: Extracts structured paragraphs and table cells using `python-docx`.
   - **TXT**: Robust multi-encoding reader (UTF-8, Latin-1, CP1252).

2. **Content Deduplication**:
   - Cryptographic SHA-256 fingerprinting.
   - Prevents duplicate chunks when ingesting identical files.
   - Replaces chunks automatically if a modified document of the same name is uploaded.

3. **Persistent Vector Storage**:
   - Backed by **ChromaDB** `PersistentClient`.
   - Data persists across server restarts in `./data/chroma_db`.

4. **Zero-Cost Local Embeddings**:
   - `sentence-transformers/all-MiniLM-L6-v2` loaded locally via Hugging Face.
   - Runs on Apple Silicon Metal Performance Shaders (`mps`) or CPU with zero embedding API cost.

5. **Strict Grounding & Hallucination Guardrails**:
   - Explicit system prompt instructions forcing the LLM to rely **only** on retrieved context.
   - Inline and structured citations: `[Document: <filename>, Page: <page>]`.
   - Clear fallback message when requested information is not present in the indexed documents.

6. **Interactive Streamlit Web Interface**:
   - Modern chat interface with conversation history.
   - Real-time ingestion progress and status badges.
   - Collapsible source citations showing document name, page number, chunk index, and snippet preview.
   - Vector database management (view documents, delete individual files, wipe database).

---

## Project Structure

```
rag-application/
├── app.py                     # Streamlit frontend application
├── config.py                  # Centralized configuration & environment loader
├── schema.py                  # Core Document schema definition
├── requirements.txt           # Pinned Python package dependencies
├── .env.example               # Environment variable template
├── README.md                  # System documentation
│
├── ingestion/                 # Pipeline 1: Document Ingestion
│   ├── __init__.py
│   ├── document_loader.py     # PDF, DOCX, TXT extractors with metadata
│   ├── text_splitter.py       # RecursiveCharacterTextSplitter wrapper
│   ├── deduplication.py       # SHA-256 document deduplication engine
│   └── pipeline.py            # End-to-end ingestion orchestrator
│
├── vectorstore/               # Vector Database Management
│   ├── __init__.py
│   ├── embeddings.py          # HuggingFace Embeddings wrapper (MPS/CPU)
│   └── store.py               # Persistent ChromaDB store & document manager
│
├── chatbot/                   # Pipeline 2: Grounded Chatbot
│   ├── __init__.py
│   ├── prompts.py             # System prompt & citation templates
│   ├── retriever.py           # Semantic search & score filtering
│   └── chain.py               # Gemini LLM integration & answer generator
│
├── data/
│   ├── chroma_db/             # Persistent vector store directory
│   └── sample_docs/           # Sample PDF, DOCX, and TXT files for testing
│
├── test_ingestion.py          # Standalone ingestion pipeline tests
├── test_chatbot.py            # Standalone chatbot & retrieval tests
└── test_e2e.py                # Full integration, grounding & persistence tests
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13 macOS arm64)

### 2. Virtual Environment Setup
```bash
# Navigate to project directory
cd /Users/mikey/rag-application

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and provide your Gemini API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-2.5-flash
DEFAULT_CHUNK_SIZE=800
DEFAULT_CHUNK_OVERLAP=150
DEFAULT_TOP_K=4
```
*(Note: You can also enter or update your Gemini API key directly in the Streamlit UI sidebar at runtime).*

---

## Verification & Testing

Every pipeline has standalone and integrated verification test suites:

### 1. Test Ingestion Pipeline Independently
Tests file extraction across PDF/DOCX/TXT, recursive chunking, metadata enrichment, duplicate detection, and ChromaDB insertion:
```bash
python3 test_ingestion.py
```

### 2. Test Chatbot & Retrieval Independently
Tests semantic similarity search against indexed chunks, page-specific retrieval, prompt construction, and citation generation:
```bash
python3 test_chatbot.py
```

### 3. Run Full End-to-End Integration Suite
Tests the complete lifecycle: clean database wipe, multi-format ingestion, grounded query answering, citation verification, document deletion, re-indexing, and persistence across simulated process restarts:
```bash
python3 test_e2e.py
```

---

## Launching the Web Interface

Launch the Streamlit dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### Using the App:
1. **Upload Documents**: Drag and drop PDF, DOCX, or TXT files in the sidebar and click **Ingest Files** (or click **Load Samples**).
2. **Chat**: Ask questions in the chat input. The assistant returns answers strictly grounded in your documents.
3. **Inspect Citations**: Click **Source Citations** under any response to view the exact document name, page number, similarity score, and text snippet.
4. **Manage Storage**: Review all indexed documents in the sidebar and delete individual documents or clear the database anytime.
