"""
FortressRAG Walkthrough (FAISS) — bare minimum, step-by-step.
Run: python rag_test.py
"""

import time
from app.tenancy import Tenancy
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, TOP_N
from app.ingestion import build_records_from_pdf
from app.embedding import ingest_into_namespace
from app.retrieval import search
from app.reranker import rerank
from app.generation import generate_answer

TENANT = "alturatech"
DEPT = "finance"
USER = "lavanya"
COLLECTION = "kb"

DOC_ID = "apple_q24"
VERSION = "1"
DOC_PATH = "docs/Apple_Q24.pdf"

QUESTION = "What was Apple's total revenue in Q4 2024?"

print("\n✅ STEP 0: Tenancy")
tenancy = Tenancy(TENANT, DEPT, USER, COLLECTION)
print("Namespace:", tenancy.namespace)

print("\n📖 STEP 1-2: Extract + chunk")
meta = build_records_from_pdf(DOC_PATH, CHUNK_SIZE, CHUNK_OVERLAP, DOC_ID, VERSION)
print("Pages:", meta["pages_count"], "Chunks:", meta["chunks_count"])

print("\n📦 STEP 3: Ingest into FAISS namespace index")
out = ingest_into_namespace(tenancy, meta)
print(out)

print(f"\n🔍 STEP 4: Retrieval Top-{TOP_K}")
t0 = time.perf_counter()
retrieved = search(tenancy, QUESTION, top_k=TOP_K)
t1 = time.perf_counter()
print("Retrieved:", len(retrieved), "latency(ms):", round((t1 - t0) * 1000, 2))

for i, r in enumerate(retrieved[:5], 1):
    print(f"  [{i}] score={r['score']:.4f} | {r['source']} p.{r.get('pages','')}")
    print("      ", r["chunk_text"][:120], "...\n")

print(f"🔀 STEP 5: Rerank Top-{TOP_N}")
t2 = time.perf_counter()
reranked = rerank(QUESTION, retrieved, top_n=TOP_N)
t3 = time.perf_counter()
print("Reranked:", len(reranked), "latency(ms):", round((t3 - t2) * 1000, 2))

print("\n💬 STEP 6: Generate Answer")
t4 = time.perf_counter()
answer = generate_answer(QUESTION, reranked)
t5 = time.perf_counter()
print("Generation latency(ms):", round((t5 - t4) * 1000, 2))

print("\n" + "=" * 70)
print("Q:", QUESTION)
print("=" * 70)
print(answer)
print("=" * 70)

print("\nSources used:")
for i, c in enumerate(reranked, 1):
    print(f"  [{i}] {c['source']}, p.{c.get('pages','')} (score: {c['score']:.4f})")