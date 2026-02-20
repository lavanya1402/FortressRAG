import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from .tenancy import Tenancy
from .config import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, TOP_N
from .ingestion import build_records_from_pdf
from .embedding import ingest_into_namespace
from .retrieval import search
from .reranker import rerank
from .generation import generate_answer

app = FastAPI(
    title="FortressRAG — Multi-Dept Classic RAG (FAISS)",
    version="1.0.0",
)

class IngestRequest(BaseModel):
    tenant_id: str
    dept_id: str
    user_id: str
    doc_id: str
    version: str
    file_path: str
    collection: str = "knowledgebase"

class IngestResponse(BaseModel):
    status: str
    message: str
    namespace: Optional[str] = None
    doc_id: Optional[str] = None
    version: Optional[str] = None
    chunks: int = 0

class ChatRequest(BaseModel):
    tenant_id: str
    dept_id: str
    user_id: str
    question: str
    collection: str = "knowledgebase"
    use_reranker: bool = True
    top_k: int = TOP_K
    top_n: int = TOP_N
    debug: bool = False

class SourceChunk(BaseModel):
    id: str
    score: float
    source: str
    pages: str
    chunk_text: str
    citation: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    latency_ms: dict
    retrieved: Optional[List[SourceChunk]] = None
    reranked: Optional[List[SourceChunk]] = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    try:
        tenancy = Tenancy(req.tenant_id, req.dept_id, req.user_id, req.collection)

        meta = build_records_from_pdf(
            pdf_path=req.file_path,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            doc_id=req.doc_id,
            version=req.version,
        )

        out = ingest_into_namespace(tenancy, meta)
        return IngestResponse(
            status=out["status"],
            message=out["message"],
            namespace=out.get("namespace"),
            doc_id=out.get("doc_id"),
            version=out.get("version"),
            chunks=out.get("chunks", 0),
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _pack(items: List[dict]) -> List[SourceChunk]:
    out = []
    for i, c in enumerate(items, 1):
        out.append(SourceChunk(
            id=c.get("id",""),
            score=float(c.get("score", 0.0)),
            source=c.get("source",""),
            pages=c.get("pages",""),
            chunk_text=(c.get("chunk_text","")[:200] + "...") if c.get("chunk_text") else "",
            citation=f"[{i}]",
        ))
    return out

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    t0 = time.perf_counter()
    try:
        tenancy = Tenancy(req.tenant_id, req.dept_id, req.user_id, req.collection)

        t_retr0 = time.perf_counter()
        retrieved = search(tenancy, req.question, top_k=req.top_k)
        t_retr1 = time.perf_counter()

        if not retrieved:
            return ChatResponse(
                answer="Not found in the provided documents.",
                sources=[],
                latency_ms={
                    "retrieval": round((t_retr1 - t_retr0) * 1000, 2),
                    "rerank": 0.0,
                    "generation": 0.0,
                    "total": round((time.perf_counter() - t0) * 1000, 2),
                },
            )

        t_rr0 = time.perf_counter()
        if req.use_reranker:
            reranked = rerank(req.question, retrieved, top_n=req.top_n)
            chunks = reranked
        else:
            reranked = []
            chunks = retrieved[:req.top_n]
        t_rr1 = time.perf_counter()

        t_gen0 = time.perf_counter()
        answer = generate_answer(req.question, chunks)
        t_gen1 = time.perf_counter()

        resp = ChatResponse(
            answer=answer,
            sources=_pack(chunks),
            latency_ms={
                "retrieval": round((t_retr1 - t_retr0) * 1000, 2),
                "rerank": round((t_rr1 - t_rr0) * 1000, 2),
                "generation": round((t_gen1 - t_gen0) * 1000, 2),
                "total": round((time.perf_counter() - t0) * 1000, 2),
            },
        )

        if req.debug:
            resp.retrieved = _pack(retrieved)
            resp.reranked = _pack(reranked) if req.use_reranker else None

        return resp

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))