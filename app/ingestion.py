import os
import re
import hashlib
from typing import List, Dict, Any
from pypdf import PdfReader

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def extract_pdf_pages(pdf_path: str) -> List[Dict[str, Any]]:
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        cleaned = re.sub(r"\s+", " ", text).strip()
        if cleaned:
            pages.append({"page": i + 1, "text": cleaned})
    return pages

def chunk_with_page_tracking(
    pages: List[Dict[str, Any]],
    chunk_size: int,
    chunk_overlap: int
) -> List[Dict[str, str]]:
    # Flatten pages into full_text and track which char belongs to which page
    full_text = ""
    char_to_page = []

    for p in pages:
        if full_text:
            full_text += " "
            char_to_page.append(p["page"])
        full_text += p["text"]
        char_to_page.extend([p["page"]] * len(p["text"]))

    chunks = []
    start = 0
    step = max(1, chunk_size - chunk_overlap)

    while start < len(full_text):
        end = min(start + chunk_size, len(full_text))
        chunk_text = full_text[start:end].strip()
        if chunk_text:
            page_set = sorted(set(char_to_page[start:end]))
            chunks.append({
                "chunk_text": chunk_text,
                "pages": ",".join(str(x) for x in page_set),
            })
        start += step

    return chunks

def build_records_from_pdf(
    pdf_path: str,
    chunk_size: int,
    chunk_overlap: int,
    doc_id: str,
    version: str
) -> Dict[str, Any]:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)

    pages = extract_pdf_pages(pdf_path)
    chunks = chunk_with_page_tracking(pages, chunk_size, chunk_overlap)

    file_name = os.path.basename(pdf_path)
    doc_hash = sha256_file(pdf_path)

    records = []
    for i, c in enumerate(chunks):
        records.append({
            "id": f"{doc_id}::v{version}::chunk-{i}",
            "doc_id": doc_id,
            "version": str(version),
            "doc_hash": doc_hash,
            "source": file_name,
            "pages": c["pages"],
            "chunk_id": i,
            "chunk_text": c["chunk_text"],
            "status": "ACTIVE",
        })

    return {
        "file_name": file_name,
        "doc_hash": doc_hash,
        "pages_count": len(pages),
        "chunks_count": len(records),
        "records": records,
    }