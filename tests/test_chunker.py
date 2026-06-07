"""Tests for core/memory/chunker.py — HTML extraction and fixed-size chunking."""

from pathlib import Path

from core.memory.chunker import chunk_text, extract_text

FIXTURE = Path(__file__).parent / "fixtures" / "sample_artifact.html"

BOILERPLATE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
  <nav><a href="/">Home</a> <a href="/about">About</a></nav>
  <header><h1>Site Header</h1></header>
  <main>
    <article>
      <h1>The Real Article Title</h1>
      <p>This is the first substantive paragraph of the article. It contains real content
      that a reader would want to extract. The text goes on for a while to make sure
      we have enough content to work with.</p>
      <p>Here is a second paragraph with more content. It discusses important topics
      in depth and provides valuable information to the reader.</p>
    </article>
  </main>
  <footer>Copyright 2024. All rights reserved. Privacy Policy. Terms of Service.</footer>
</body>
</html>"""

LONG_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Pack my box with five dozen liquor jugs. "
    "How vexingly quick daft zebras jump. "
    "The five boxing wizards jump quickly. "
) * 20  # ~740 chars * 20 = ~14800 chars total


# --- extract_text ---


def test_extract_text_real_fixture():
    html = FIXTURE.read_text(encoding="utf-8")
    result = extract_text(html)
    assert isinstance(result, str)
    assert len(result) > 0


def test_extract_text_empty_input():
    assert extract_text("") == ""


def test_extract_text_strips_boilerplate():
    raw_text_len = len(BOILERPLATE_HTML)
    result = extract_text(BOILERPLATE_HTML)
    assert len(result) < raw_text_len


# --- chunk_text ---


def test_chunk_text_char_offset_invariant():
    chunks = chunk_text(LONG_TEXT)
    assert len(chunks) > 1
    for c in chunks:
        assert c.char_start + len(c.text) == c.char_end, (
            f"Invariant failed: chunk {c.ordinal} char_start={c.char_start} "
            f"len={len(c.text)} char_end={c.char_end}"
        )


def test_chunk_text_size_bound():
    chunks = chunk_text(LONG_TEXT, chunk_size=800)
    for c in chunks:
        assert len(c.text) <= 800 + 200, (
            f"Chunk {c.ordinal} exceeded size bound: {len(c.text)} chars"
        )


def test_chunk_text_ordinals_sequential():
    chunks = chunk_text(LONG_TEXT)
    for i, c in enumerate(chunks):
        assert c.ordinal == i


def test_chunk_text_overlap():
    chunks = chunk_text(LONG_TEXT, chunk_size=800, overlap=100)
    assert len(chunks) > 1
    for i in range(len(chunks) - 1):
        cur_end = chunks[i].char_end
        next_start = chunks[i + 1].char_start
        # next chunk starts before current chunk ends (overlap)
        assert next_start < cur_end, (
            f"No overlap between chunk {i} and {i + 1}: cur_end={cur_end} next_start={next_start}"
        )


def test_chunk_text_empty_input():
    assert chunk_text("") == []


def test_chunk_text_whitespace_input():
    assert chunk_text("   \n\t  ") == []


def test_chunk_text_short_text_single_chunk():
    short = "This is a short sentence. It fits in one chunk."
    chunks = chunk_text(short, chunk_size=800)
    assert len(chunks) == 1
    assert chunks[0].char_start == 0
    assert chunks[0].char_end == len(short)
    assert chunks[0].ordinal == 0
    assert chunks[0].char_start + len(chunks[0].text) == chunks[0].char_end
