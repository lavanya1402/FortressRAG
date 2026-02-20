import os
import json
import time
from typing import Dict, Any, List
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from .config import OPENAI_API_KEY, EMBED_MODEL
from .tenancy import Tenancy

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def load_manifest(path: str) -> Dict[str, Any]:
    _ensure_dir(os.path.dirname(path))
    if not os.path.exists(path):
        return {"docs": {}, "updated_at": None}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_manifest(path: str, m: Dict[str, Any]) -> None:
    _ensure_dir(os.path.dirname(path))
    m["updated_at"] = int(time.time())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=2)

def _load_or_create_index(index_dir: str, embeddings: OpenAIEmbeddings) -> FAISS:
    if os.path.exists(index_dir):
        return FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)

    # Create a tiny starter index (so add_documents works even on first run)
    starter = FAISS.from_texts(["init"], embeddings, metadatas=[{"source": "init", "id": "init"}])
    _ensure_dir(index_dir)
    starter.save_local(index_dir)
    return starter

def ingest_into_namespace(tenancy: Tenancy, doc_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enterprise-friendly ingestion strategy:

    - Duplicate detection: if ACTIVE hash matches -> skip.
    - Version strategy: manifest keeps versions; old ACTIVE becomes DEPRECATED.
    - Lifecycle: ACTIVE/DEPRECATED tracked in manifest.
    - Index strategy (FAISS): append new ACTIVE chunks; for strict cleanup, scheduled rebuild can be used.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing in .env")

    records = doc_meta.get("records", [])
    if not records:
        raise ValueError("No chunks created (empty PDF text?)")

    doc_id = records[0]["doc_id"]
    version = records[0]["version"]
    doc_hash = doc_meta["doc_hash"]
    source = doc_meta["file_name"]

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, api_key=OPENAI_API_KEY)

    # Manifest (governance)
    manifest = load_manifest(tenancy.manifest_path)
    docs = manifest.setdefault("docs", {})
    entry = docs.setdefault(doc_id, {"versions": {}, "active_version": None, "active_doc_hash": None, "source": source})

    # Duplicate detection
    if entry.get("active_doc_hash") == doc_hash:
        return {
            "status": "SKIPPED_DUPLICATE",
            "message": f"'{doc_id}' already ingested (same hash).",
            "namespace": tenancy.namespace,
            "doc_id": doc_id,
            "version": entry.get("active_version"),
            "chunks": 0,
        }

    # Deprecate previous version (if any)
    prev_active = entry.get("active_version")
    if prev_active:
        prev = entry["versions"].setdefault(str(prev_active), {})
        prev["status"] = "DEPRECATED"
        prev["deprecated_at"] = int(time.time())

    # Activate new version
    entry["versions"][str(version)] = {
        "doc_hash": doc_hash,
        "source": source,
        "chunks": len(records),
        "status": "ACTIVE",
        "ingested_at": int(time.time()),
    }
    entry["active_version"] = str(version)
    entry["active_doc_hash"] = doc_hash
    entry["source"] = source
    docs[doc_id] = entry

    save_manifest(tenancy.manifest_path, manifest)

    # FAISS index append
    index_dir = tenancy.index_dir_current
    db = _load_or_create_index(index_dir, embeddings)

    new_docs: List[Document] = []
    for r in records:
        new_docs.append(
            Document(
                page_content=r["chunk_text"],
                metadata={
                    "id": r["id"],
                    "doc_id": r["doc_id"],
                    "version": r["version"],
                    "doc_hash": r["doc_hash"],
                    "source": r["source"],
                    "pages": r.get("pages", ""),
                    "chunk_id": r.get("chunk_id", 0),
                    "status": "ACTIVE",
                },
            )
        )

    db.add_documents(new_docs)
    _ensure_dir(index_dir)
    db.save_local(index_dir)

    return {
        "status": "INGESTED",
        "message": "Ingested OK (manifest updated; FAISS index updated).",
        "namespace": tenancy.namespace,
        "doc_id": doc_id,
        "version": version,
        "chunks": len(new_docs),
        "index_dir": index_dir,
    }