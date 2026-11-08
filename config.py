import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
SAMPLE_DOCS_DIR = DATA_DIR / "sample_docs"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DOCS_DIR.mkdir(parents=True, exist_ok=True)

# ChromaDB Configuration
CHROMA_COLLECTION_NAME = "rag_documents"

# Embedding Configuration (HuggingFace)
# Default model: sentence-transformers/all-MiniLM-L6-v2 (fast, high-quality 384-dim dense vectors)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Text Chunking Defaults
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", 800))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", 150))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", 4))

# LLM Configuration (Gemini API)
# Check both GEMINI_API_KEY and GOOGLE_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# LLM Hyperparameters
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 1024))
