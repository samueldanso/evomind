"""Agent API routes — dispatch, status, message, run history."""

from __future__ import annotations

import dataclasses
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.governance import audit
from core.agents.teaching import run_teaching_turn
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

        result = dispatch(task, db, provider, auto_teach=False)
        research_run_dict = _run_to_dict(result)

        teach_run_dict = None
        if auto_teach and result.status == "complete" and result.output:
            artifact_slug = result.output.get("artifact_slug")
            if artifact_slug:
                teach_task = TeachTask(
                    task_type="teach",
                    topic=topic,
                    artifact_slug=artifact_slug,
                )
                teach_run_dict = _start_interactive_teach(db, provider, request, teach_task)

        return {"run": research_run_dict, "teach_run": teach_run_dict}

    else:
        task = TeachTask(
            task_type="teach",
            topic=topic,
            artifact_slug=body.get("artifact_slug"),
            mastery_context=body.get("mastery_context"),
        )
        teach_run_dict = _start_interactive_teach(db, provider, request, task)
        return {"run": teach_run_dict, "teach_run": None}


def _start_interactive_teach(db, provider, request: Request, task: TeachTask) -> dict:
    """Start interactive teaching: run opening layer, pause, return run dict."""
    run_id = audit.create_run(db, "teaching_agent", {
        "task_type": "teach",
        "topic": task.topic,
        "artifact_slug": task.artifact_slug,
        "mastery_context": task.mastery_context,
    })

    call_tool = _build_call_tool(db, provider, request)
    try:
        result = run_teaching_turn(task, None, None, call_tool)
    except Exception as e:
        audit.fail_run(db, run_id, str(e), cost_tokens=0, cost_usd=0.0)
        run = audit.get_run(db, run_id)
        return run

    audit.pause_run(db, run_id, result["session_log"])
    run = audit.get_run(db, run_id)
    return run


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

    if run["status"] != "paused_awaiting_input":
        return JSONResponse(
            status_code=409,
            content={"error": f"Run status is '{run['status']}', expected 'paused_awaiting_input'"},
        )

    provider = request.app.state.provider
    session_log = run.get("session_log") or []
    task_input = run.get("task_input", {})
    task = TeachTask(
        task_type="teach",
        topic=task_input.get("topic", ""),
        artifact_slug=task_input.get("artifact_slug"),
        mastery_context=task_input.get("mastery_context"),
    )

    audit.resume_run(db, run_id)

    call_tool = _build_call_tool(db, provider, request)
    try:
        result = run_teaching_turn(task, content, session_log, call_tool)
    except Exception as e:
        audit.fail_run(db, run_id, str(e), cost_tokens=0, cost_usd=0.0)
        return JSONResponse(status_code=500, content={"error": str(e)})

    if result["done"]:
        output = {"checklist_slug": result.get("checklist_slug", "")}
        audit.complete_run(db, run_id, output, cost_tokens=0, cost_usd=0.0)
        return {
            "reply": result["reply"],
            "status": "complete",
            "session_log_length": len(result["session_log"]),
        }

    audit.pause_run(db, run_id, result["session_log"])
    return {
        "reply": result["reply"],
        "status": "teaching",
        "session_log_length": len(result["session_log"]),
    }


def _build_call_tool(db, provider, request: Request):
    """Build a call_tool closure for the teaching turn."""
    from core.tools.retrieve import build_retrieve_tool
    from core.tools.generate import build_generate_tool
    from core.tools.ingest import build_ingest_tool
    from pathlib import Path

    vault_path = Path(os.environ.get(
        "EVO_RESEARCH_STORE",
        str(Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian"
            / "Documents" / "Samuel's Vault" / "SamuelOS" / "Knowledge" / "Research")
    ))

    tools = {
        "retrieve": build_retrieve_tool(db, provider),
        "generate": build_generate_tool(provider),
        "ingest": build_ingest_tool(db, vault_path),
    }

    def call_tool(name: str, inp: dict) -> dict:
        tool = tools.get(name)
        if tool is None:
            return {"error": f"Unknown tool: {name}"}
        return tool.execute(inp)

    return call_tool
