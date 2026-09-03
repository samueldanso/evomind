"""EvoMind FastAPI server — agent + chat endpoints."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.llm.bedrock import get_provider
from core.memory.db import default_db_path, load_sqlite_vec, open_db
from server.routes.agent import router as agent_router
from server.routes.artifacts import router as artifacts_router
from server.routes.chat import router as chat_router
from server.routes.ingest import router as ingest_router
from server.routes.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = default_db_path()
    try:
        conn = open_db(db_path)
        load_sqlite_vec(conn)
    except Exception as exc:
        raise RuntimeError(f"Failed to open database: {exc}") from exc

    try:
        provider = get_provider()
    except ValueError as exc:
        app.state.startup_error = f"Provider init failed: {exc}"
        app.state.db = None
        app.state.provider = None
        yield
        return

    app.state.db = conn
    app.state.provider = provider
    app.state.startup_error = None
    app.state.db_path = str(db_path)
    yield
    conn.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.environ.get("ALLOWED_ORIGIN", ""),
    ],
    allow_methods=["POST", "GET", "DELETE", "OPTIONS"],
    allow_headers=["content-type"],
)

app.include_router(artifacts_router)
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(ingest_router)
app.include_router(upload_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("EVO_CHAT_PORT", "8765")))
