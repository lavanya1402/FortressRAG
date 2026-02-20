from typing import List, Dict
from langchain_openai import ChatOpenAI
from .config import OPENAI_API_KEY, LLM_MODEL

def generate_answer(question: str, chunks: List[Dict]) -> str:
    if not chunks:
        return "Not found in the provided documents."

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing in .env")

    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.2,
        max_tokens=900,
    )

    context_parts = []
    for i, c in enumerate(chunks, 1):
        pages = c.get("pages", "")
        page_label = f", p.{pages}" if pages else ""
        context_parts.append(f"[{i}] (source: {c.get('source','')}{page_label})\n{c.get('chunk_text','')}")

    context = "\n\n".join(context_parts)

    system = (
        "You are an enterprise knowledge assistant. "
        "Answer ONLY using the provided context. "
        "If the answer is not present, reply exactly: 'Not found in the provided documents.' "
        "Cite sources inline as [1], [2], etc. "
        "End with a References section listing: [n] filename, p.X"
    )

    msg = llm.invoke([
        ("system", system),
        ("human", f"Context:\n{context}\n\n---\nQuestion: {question}")
    ])

    return msg.content