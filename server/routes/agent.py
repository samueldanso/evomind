"""Agent API routes — dispatch, status, message, run history."""

from __future__ import annotations

import dataclasses

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.governance import audit
from core.runtime.contracts import AgentRun, ResearchTask, TeachTask
from core.runtime.dispatcher import dispatch

router = APIRouter(prefix="/api/agent")


def _run_to_dict(run: AgentRun) -> dict:
    """Convert AgentRun dataclass to JSON-serializable dict."""
    d = dataclasses.asdict(run)
    return d


@router.post("")
async def dispatch_agent(request: Request):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    body = await request.json()
    task_type = body.get("task_type")
    topic = body.get("topic")

    if not task_type or task_type not in ("research", "teach"):
        return JSONResponse(
            status_code=422,
            content={"error": "task_type must be 'research' or 'teach'"},
        )
    if not topic or not str(topic).strip():
        return JSONResponse(
            status_code=422,
            content={"error": "topic is required and must be non-empty"},
        )

    db = request.app.state.db
    provider = request.app.state.provider
    auto_teach = body.get("auto_teach", True)

    if task_type == "research":
        task = ResearchTask(
            task_type="research",
            topic=topic,
            mode=body.get("mode", "concept"),
            context=body.get("context"),
        )
    else:
        task = TeachTask(
            task_type="teach",
            topic=topic,
            artifact_slug=body.get("artifact_slug"),
            mastery_context=body.get("mastery_context"),
        )

    result = dispatch(task, db, provider, auto_teach=auto_teach)

    if isinstance(result, tuple):
        research_run, teach_run = result
        return {
            "run": _run_to_dict(research_run),
            "teach_run": _run_to_dict(teach_run),
        }
    else:
        return {
            "run": _run_to_dict(result),
            "teach_run": None,
        }


@router.get("/runs")
async def list_runs(request: Request):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db = request.app.state.db
    limit_str = request.query_params.get("limit", "20")
    try:
        limit = max(1, min(100, int(limit_str)))
    except (ValueError, TypeError):
        limit = 20

    runs = audit.list_runs(db, limit=limit)
    return {"runs": runs}


@router.get("/{run_id}")
async def get_run(request: Request, run_id: int):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db = request.app.state.db
    run = audit.get_run(db, run_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "Run not found"})
    return {"run": run}


@router.post("/{run_id}/message")
async def post_message(request: Request, run_id: int):
    if getattr(request.app.state, "startup_error", None):
        return JSONResponse(
            status_code=503,
            content={"error": request.app.state.startup_error},
        )

    db = request.app.state.db
    body = await request.json()
    content = body.get("content")

    if not content or not str(content).strip():
        return JSONResponse(
            status_code=422,
            content={"error": "content is required and must be non-empty"},
        )

    run = audit.get_run(db, run_id)
    if run is None:
        return JSONResponse(status_code=404, content={"error": "Run not found"})

    return {
        "reply": "Teaching session turn delivery is Phase D.1 (WebSocket upgrade). Use CLI for multi-turn sessions.",
        "status": "teaching",
    }
