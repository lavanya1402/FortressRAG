from typing import List, Dict
from langchain_openai import ChatOpenAI
from .config import OPENAI_API_KEY, LLM_MODEL, TOP_N

def rerank(question: str, retrieved: List[Dict], top_n: int = TOP_N) -> List[Dict]:
    if not retrieved:
        return []

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing in .env")

    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.0,
        max_tokens=200,
    )

    candidates = []
    for i, r in enumerate(retrieved, 1):
        candidates.append(
            f"[{i}] source={r.get('source','')}, pages={r.get('pages','')}\n"
            f"{r.get('chunk_text','')[:700]}"
        )

    prompt = f"""
You are a strict reranker for RAG.
Question: {question}

Select the TOP {top_n} candidate numbers in best-first order.
Return ONLY comma-separated numbers (example: 3,1,2). No extra text.

Candidates:
{chr(10).join(candidates)}
""".strip()

    resp = llm.invoke([("human", prompt)]).content.strip()

    nums = [x.strip() for x in resp.split(",") if x.strip().isdigit()]
    picked_indices = []
    for n in nums:
        idx = int(n) - 1
        if 0 <= idx < len(retrieved) and idx not in picked_indices:
            picked_indices.append(idx)
        if len(picked_indices) >= top_n:
            break

    if not picked_indices:
        picked_indices = list(range(min(top_n, len(retrieved))))

    return [retrieved[i] for i in picked_indices]