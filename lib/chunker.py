"""HTML text extraction and fixed-size chunking with sentence-boundary respect."""

from dataclasses import dataclass

from bs4 import BeautifulSoup

try:
    import trafilatura

    _TRAFILATURA = True
except ImportError:
    _TRAFILATURA = False


@dataclass
class Chunk:
    text: str
    char_start: int
    char_end: int
    ordinal: int


def extract_text(html: str) -> str:
    """Extract plain body text from HTML, stripping nav/header/footer boilerplate."""
    if not html or not html.strip():
        return ""

    if _TRAFILATURA:
        result = trafilatura.extract(html)
        if result:
            return result

    # BS4 fallback
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    return text if text else ""


def _next_sentence_boundary(text: str, pos: int) -> int:
    """Return the position just after the next sentence boundary at or after pos."""
    for i in range(pos, len(text)):
        if text[i] == "\n":
            return i + 1
        if text[i] == "." and i + 1 < len(text) and text[i + 1] == " ":
            return i + 2
    return len(text)


def _prev_sentence_boundary(text: str, pos: int) -> int:
    """Return the position just after the nearest sentence boundary at or before pos."""
    for i in range(pos, -1, -1):
        if i < len(text) and text[i] == "\n":
            return i + 1
        if i < len(text) and text[i] == "." and i + 1 < len(text) and text[i + 1] == " ":
            return i + 2
        if i > 0 and text[i - 1] == "." and text[i] == " ":
            return i + 1
    return 0


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[Chunk]:
    """Split text into fixed-size chunks with sentence-boundary respect and overlap."""
    if not text or not text.strip():
        return []

    # Short text fits in one chunk
    if len(text) <= chunk_size:
        return [Chunk(text=text, char_start=0, char_end=len(text), ordinal=0)]

    chunks: list[Chunk] = []
    start = 0
    ordinal = 0

    while start < len(text):
        # Extend to next sentence boundary after chunk_size
        target = start + chunk_size
        if target >= len(text):
            end = len(text)
        else:
            end = _next_sentence_boundary(text, target)

        chunk_text_str = text[start:end]
        chunks.append(
            Chunk(
                text=chunk_text_str,
                char_start=start,
                char_end=end,
                ordinal=ordinal,
            )
        )
        ordinal += 1

        if end >= len(text):
            break

        # Compute next start: rewind overlap chars from end, snap to sentence boundary
        overlap_pos = end - overlap
        if overlap_pos <= start:
            overlap_pos = start + 1  # always advance to prevent infinite loop

        next_start = _prev_sentence_boundary(text, overlap_pos)
        if next_start <= start:
            # No sentence boundary found before overlap_pos; just use overlap_pos
            next_start = overlap_pos

        start = next_start

    return chunks
