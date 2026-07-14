"""
Multi-Modal RAG System (lightweight edition).

Retrieves relevant chunks from a local knowledge base (DSA sheets, system
design notes, company-specific question banks, behavioral frameworks) using
TF-IDF + cosine similarity. This avoids downloading large embedding models,
so it runs anywhere with just scikit-learn.

Swap `TfidfVectorizer` for a sentence-transformers embedding index (or
ChromaDB/FAISS, as named in the original spec) as a drop-in production
upgrade — the `retrieve()` interface stays the same either way.
"""
import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "kb")

_chunks = []       # list of {"source": filename, "text": chunk}
_vectorizer = None
_matrix = None


def _chunk_text(text: str, size: int = 500, overlap: int = 100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def build_index():
    global _chunks, _vectorizer, _matrix
    _chunks = []
    for path in glob.glob(os.path.join(KB_DIR, "*.md")):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for chunk in _chunk_text(text):
            if chunk.strip():
                _chunks.append({"source": os.path.basename(path), "text": chunk.strip()})

    if not _chunks:
        _vectorizer, _matrix = None, None
        return

    _vectorizer = TfidfVectorizer(stop_words="english")
    _matrix = _vectorizer.fit_transform([c["text"] for c in _chunks])


def retrieve(query: str, k: int = 4) -> list:
    """Return the top-k most relevant knowledge base chunks for a query."""
    if _vectorizer is None:
        build_index()
    if _vectorizer is None or not _chunks:
        return []

    q_vec = _vectorizer.transform([query])
    sims = cosine_similarity(q_vec, _matrix).flatten()
    top_idx = sims.argsort()[::-1][:k]
    return [
        {**_chunks[i], "score": float(sims[i])}
        for i in top_idx if sims[i] > 0
    ]


build_index()
