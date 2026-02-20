import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from project root

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Models
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()

# Chunking (character-based, simple & deterministic)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Retrieval & rerank
TOP_K = int(os.getenv("TOP_K", "8"))
TOP_N = int(os.getenv("TOP_N", "4"))

# Storage
STORAGE_ROOT = os.getenv("STORAGE_ROOT", "storage").strip()

# Tenancy mode:
# dept = shared index per dept (cost-effective)
# user = per-user index (maximum isolation)
TENANCY_MODE = os.getenv("TENANCY_MODE", "dept").strip().lower()
if TENANCY_MODE not in ("dept", "user"):
    TENANCY_MODE = "dept"