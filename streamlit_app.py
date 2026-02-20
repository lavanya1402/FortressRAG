import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.tenancy import Tenancy
from app.config import CHUNK_SIZE, CHUNK_OVERLAP, TOP_K, TOP_N
from app.ingestion import build_records_from_pdf
from app.embedding import ingest_into_namespace
from app.retrieval import search
from app.reranker import rerank
from app.generation import generate_answer

st.set_page_config(page_title="FortressRAG UI", layout="wide")
st.title("🏰 FortressRAG — Multi-Dept RAG (FAISS)")

# ----------------------------
# Sidebar: Tenancy Controls
# ----------------------------
st.sidebar.header("Tenancy")
tenant_id = st.sidebar.text_input("tenant_id", value="alturatech")
dept_id   = st.sidebar.text_input("dept_id", value="finance")
user_id   = st.sidebar.text_input("user_id", value="lavanya")
collection = st.sidebar.text_input("collection", value="kb")

tenancy = Tenancy(tenant_id, dept_id, user_id, collection)
st.sidebar.success(f"Namespace:\n{tenancy.namespace}")

st.sidebar.divider()
st.sidebar.header("Doc Settings")
doc_id = st.sidebar.text_input("doc_id", value="apple_q24")
version = st.sidebar.text_input("version", value="1")

use_reranker = st.sidebar.toggle("Use reranker", value=True)
top_k = st.sidebar.number_input("Top-K (retrieval)", min_value=1, max_value=30, value=TOP_K)
top_n = st.sidebar.number_input("Top-N (rerank/use)", min_value=1, max_value=10, value=TOP_N)

# ----------------------------
# Ingest Section
# ----------------------------
st.subheader("📥 Ingest a PDF")
uploaded = st.file_uploader("Upload PDF", type=["pdf"])

colA, colB = st.columns([1, 2])

with colA:
    ingest_btn = st.button("✅ Ingest Document", use_container_width=True)

with colB:
    st.caption("Tip: Update version to 2 if you re-upload updated PDF (Version strategy demo).")

if ingest_btn:
    if not uploaded:
        st.error("Please upload a PDF first.")
    else:
        # Save uploaded pdf into docs/
        save_path = f"docs/{uploaded.name}"
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())

        st.info(f"Saved: {save_path}")

        t0 = time.perf_counter()
        meta = build_records_from_pdf(save_path, CHUNK_SIZE, CHUNK_OVERLAP, doc_id, version)
        t1 = time.perf_counter()

        out = ingest_into_namespace(tenancy, meta)
        t2 = time.perf_counter()

        st.success(out.get("message", "Done"))
        st.json({
            "status": out.get("status"),
            "namespace": out.get("namespace"),
            "doc_id": out.get("doc_id"),
            "version": out.get("version"),
            "chunks_upserted": out.get("chunks"),
            "latency_ms": {
                "extract+chunk": round((t1 - t0) * 1000, 2),
                "ingest/index": round((t2 - t1) * 1000, 2),
                "total": round((t2 - t0) * 1000, 2),
            }
        })

st.divider()

# ----------------------------
# Chat Section
# ----------------------------
st.subheader("💬 Ask a Question")
question = st.text_input("Your question", value="What was Apple's total revenue in Q4 2024?")
ask_btn = st.button("🔍 Run RAG", use_container_width=True)

if ask_btn:
    if not question.strip():
        st.error("Please enter a question.")
    else:
        t0 = time.perf_counter()
        t_retr0 = time.perf_counter()
        retrieved = search(tenancy, question, top_k=int(top_k))
        t_retr1 = time.perf_counter()

        if not retrieved:
            st.warning("No results retrieved. (Try re-ingesting or resetting storage for this namespace.)")
            st.json({
                "latency_ms": {
                    "retrieval": round((t_retr1 - t_retr0) * 1000, 2),
                    "total": round((time.perf_counter() - t0) * 1000, 2),
                }
            })
        else:
            t_rr0 = time.perf_counter()
            if use_reranker:
                chosen = rerank(question, retrieved, top_n=int(top_n))
            else:
                chosen = retrieved[: int(top_n)]
            t_rr1 = time.perf_counter()

            t_gen0 = time.perf_counter()
            answer = generate_answer(question, chosen)
            t_gen1 = time.perf_counter()

            st.markdown("### ✅ Answer")
            st.write(answer)

            st.markdown("### 📄 Sources Used")
            for i, c in enumerate(chosen, 1):
                st.write(f"**[{i}]** {c.get('source','')} | p.{c.get('pages','')} | score={c.get('score',0):.4f}")
                st.code(c.get("chunk_text", "")[:800])

            with st.expander("🔎 Debug: Retrieved Top-K"):
                for i, c in enumerate(retrieved, 1):
                    st.write(f"**[{i}]** {c.get('source','')} | p.{c.get('pages','')} | score={c.get('score',0):.4f}")
                    st.code(c.get("chunk_text", "")[:500])

            st.markdown("### ⏱️ Latency (ms)")
            st.json({
                "retrieval": round((t_retr1 - t_retr0) * 1000, 2),
                "rerank": round((t_rr1 - t_rr0) * 1000, 2),
                "generation": round((t_gen1 - t_gen0) * 1000, 2),
                "total": round((time.perf_counter() - t0) * 1000, 2),
            })