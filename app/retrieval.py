import os
from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from .config import OPENAI_API_KEY, EMBED_MODEL, TOP_K
from .tenancy import Tenancy

def search(tenancy: Tenancy, query: str, top_k: int = TOP_K) -> List[Dict]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing in .env")

    index_dir = tenancy.index_dir_current
    if not os.path.exists(index_dir):
        return []

    emb = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)
    db = FAISS.load_local(index_dir, emb, allow_dangerous_deserialization=True)

    hits = db.similarity_search_with_score(query, k=top_k)

    results = []
    for doc, score in hits:
        md = doc.metadata or {}
        results.append({
            "id": md.get("id", ""),
            "score": float(score),  # NOTE: FAISS returns distance-like score; lower can be better depending on setup
            "chunk_text": doc.page_content,
            "source": md.get("source", ""),
            "pages": md.get("pages", ""),
            "doc_id": md.get("doc_id", ""),
            "version": md.get("version", ""),
        })

    return results