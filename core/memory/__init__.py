"""Memory layer — DB helpers, chunking, and retrieval."""

from core.memory.chunker import Chunk, chunk_text, extract_text
from core.memory.db import default_db_path, load_sqlite_vec, open_db
from core.memory.retrieval import (
    RetrievalResult,
    fts_search,
    hybrid_search,
    vec_search,
)

__all__ = [
    "Chunk",
    "RetrievalResult",
    "chunk_text",
    "default_db_path",
    "extract_text",
    "fts_search",
    "hybrid_search",
    "load_sqlite_vec",
    "open_db",
    "vec_search",
]
