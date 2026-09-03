"""Upload route — extract text from PDF, DOCX, TXT, and MD files."""

from __future__ import annotations

from io import BytesIO
from pathlib import PurePath

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes using pymupdf."""
    import fitz  # pymupdf

    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages).strip()


def _extract_docx_text(data: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    from docx import Document

    doc = Document(BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs).strip()


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse(status_code=400, content={"error": "No filename provided"})

    ext = PurePath(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"},
        )

    data = await file.read()
    if not data:
        return JSONResponse(status_code=400, content={"error": "Empty file"})

    try:
        if ext == ".pdf":
            text = _extract_pdf_text(data)
        elif ext == ".docx":
            text = _extract_docx_text(data)
        else:
            # TXT / MD — decode as UTF-8
            text = data.decode("utf-8").strip()
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to extract text: {exc}"},
        )

    if not text:
        return JSONResponse(status_code=400, content={"error": "No text could be extracted from the file"})

    title = PurePath(file.filename).stem

    return {"text": text, "title": title, "filename": file.filename}
