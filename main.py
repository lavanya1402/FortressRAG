"""
FortressRAG — entry point.

Usage:
  python main.py serve

  python main.py ingest <tenant> <dept> <user> <doc_id> <version> <file_path> [collection]
  python main.py ask <tenant> <dept> <user> "<question>" [collection=...] [--no-rerank] [--debug]
"""

import sys
import os
import uvicorn

def serve():
    uvicorn.run("app.api:app", host="0.0.0.0", port=8000, reload=True)

def ingest_cmd(args):
    from app.tenancy import Tenancy
    from app.config import CHUNK_SIZE, CHUNK_OVERLAP
    from app.ingestion import build_records_from_pdf
    from app.embedding import ingest_into_namespace

    tenant, dept, user, doc_id, version, file_path = args[:6]
    collection = args[6] if len(args) > 6 and not args[6].startswith("--") else "knowledgebase"

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print("❌ File not found:", abs_path)
        return

    meta = build_records_from_pdf(abs_path, CHUNK_SIZE, CHUNK_OVERLAP, doc_id, version)
    tenancy = Tenancy(tenant, dept, user, collection)

    out = ingest_into_namespace(tenancy, meta)
    print(out)

def ask_cmd(args):
    from app.tenancy import Tenancy
    from app.retrieval import search
    from app.reranker import rerank
    from app.generation import generate_answer
    from app.config import TOP_K, TOP_N

    tenant, dept, user = args[0], args[1], args[2]

    use_reranker = True
    debug = False
    collection = "knowledgebase"
    question_parts = []

    for a in args[3:]:
        if a == "--no-rerank":
            use_reranker = False
        elif a == "--debug":
            debug = True
        elif a.startswith("collection="):
            collection = a.split("=", 1)[1]
        else:
            question_parts.append(a)

    question = " ".join(question_parts).strip().strip('"')
    tenancy = Tenancy(tenant, dept, user, collection)

    retrieved = search(tenancy, question, top_k=TOP_K)
    if debug:
        print("\n📡 Retrieved:")
        for i, r in enumerate(retrieved, 1):
            print(i, r.get("source"), r.get("pages",""), r.get("score"))

    if use_reranker:
        chunks = rerank(question, retrieved, top_n=TOP_N)
        if debug:
            print("\n🔀 Reranked:")
            for i, r in enumerate(chunks, 1):
                print(i, r.get("source"), r.get("pages",""), r.get("score"))
    else:
        chunks = retrieved[:TOP_N]

    print("\n💬 Answer:\n")
    print(generate_answer(question, chunks))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "serve":
        serve()
    elif cmd == "ingest":
        if len(sys.argv) < 8:
            print("Usage: python main.py ingest <tenant> <dept> <user> <doc_id> <version> <file_path> [collection]")
            return
        ingest_cmd(sys.argv[2:])
    elif cmd == "ask":
        if len(sys.argv) < 6:
            print('Usage: python main.py ask <tenant> <dept> <user> "<question>" [collection=...] [--no-rerank] [--debug]')
            return
        ask_cmd(sys.argv[2:])
    else:
        print("Unknown command:", cmd)
        print(__doc__)

if __name__ == "__main__":
    main()