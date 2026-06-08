"""Teaching Agent — step function for the agent execution loop."""

from __future__ import annotations

import os
import re
from typing import Callable

from core.prompts.templates import TEACH_CHECKLIST, TEACH_CONNECTIONS, TEACH_LAYER, TEACH_SYSTEM
from core.runtime.contracts import TeachTask

PHASE_OPENING = "opening"
PHASE_LAYER = "layer"
PHASE_CONNECTIONS = "connections"
PHASE_CHECKLIST = "checklist"


def run_teaching_turn(
    task: TeachTask,
    user_message: str | None,
    session_log: list[dict] | None,
    call_tool: Callable[[str, dict], dict],
) -> dict:
    """Execute a single teaching turn. Returns {reply, session_log, phase, done}.

    First call (user_message=None): runs opening layer.
    Subsequent calls: advances with user's response.
    After checklist: returns done=True.
    """
    max_turns = int(os.environ.get("EVO_TEACH_MAX_TURNS", "20"))

    if session_log is None:
        session_log = []

    if not session_log:
        query = task.artifact_slug or task.topic
        retrieve_out = call_tool("retrieve", {"query": query, "k": 8})
        kb_chunks = retrieve_out.get("results", [])
        context_text = "\n\n".join(
            f"[{r['title']}] {r['snippet']}" for r in kb_chunks
        ) or "No existing KB context."

        mastery_ctx = task.mastery_context or ""
        opening_prompt = (
            f"{TEACH_SYSTEM}\n\nTopic: {task.topic}\nKB context:\n{context_text}"
            + (f"\nLearner context: {mastery_ctx}" if mastery_ctx else "")
        )

        layer1_out = call_tool("generate", {
            "messages": [{"role": "user", "content": opening_prompt}],
            "context": kb_chunks,
        })

        reply = layer1_out.get("text", "")
        session_log.append({"role": "assistant", "content": reply})
        return {"reply": reply, "session_log": session_log, "phase": PHASE_OPENING, "done": False}

    session_log.append({"role": "user", "content": user_message})
    turn_count = sum(1 for m in session_log if m["role"] == "assistant")

    if turn_count >= max_turns:
        return _run_closing(task, session_log, call_tool)

    if turn_count >= max_turns - 2:
        return _run_connections_and_close(task, session_log, call_tool)

    layer_out = call_tool("generate", {
        "messages": [{"role": "user", "content":
            TEACH_LAYER.format(
                session_log=str(session_log[-6:]),
                user_response=user_message,
            )
        }],
        "context": [],
    })

    reply = layer_out.get("text", "")
    session_log.append({"role": "assistant", "content": reply})
    return {"reply": reply, "session_log": session_log, "phase": PHASE_LAYER, "done": False}


def _run_connections_and_close(
    task: TeachTask,
    session_log: list[dict],
    call_tool: Callable[[str, dict], dict],
) -> dict:
    """Run connections step then checklist, return final result."""
    connections_out = call_tool("generate", {
        "messages": [{"role": "user", "content":
            TEACH_CONNECTIONS.format(session_log=str(session_log[-8:]))
        }],
        "context": [],
    })
    session_log.append({"role": "assistant", "content": connections_out.get("text", "")})

    return _run_closing(task, session_log, call_tool)


def _run_closing(
    task: TeachTask,
    session_log: list[dict],
    call_tool: Callable[[str, dict], dict],
) -> dict:
    """Generate mastery checklist and ingest as artifact."""
    checklist_out = call_tool("generate", {
        "messages": [{"role": "user", "content":
            TEACH_CHECKLIST.format(topic=task.topic, session_log=str(session_log[-10:]))
        }],
        "context": [],
    })
    checklist_md = checklist_out.get("text", "")

    slug = re.sub(r"[^a-z0-9-]", "", f"{task.topic}-mastery-checklist".lower().replace(" ", "-"))[:60]
    checklist_html = (
        f"<html><body><h1>Mastery Checklist: {task.topic}</h1>"
        f"<pre>{checklist_md}</pre></body></html>"
    )

    ingest_out = call_tool("ingest", {
        "title": f"Mastery Checklist: {task.topic}",
        "slug": slug,
        "html_content": checklist_html,
        "summary": f"Mastery checklist for {task.topic} from teaching session.",
        "tags": [task.topic.lower(), "teaching", "mastery-checklist"],
    })

    reply = checklist_md
    session_log.append({"role": "assistant", "content": reply})

    return {
        "reply": reply,
        "session_log": session_log,
        "phase": PHASE_CHECKLIST,
        "done": True,
        "checklist_slug": ingest_out.get("slug", slug),
    }


def run_teaching_agent(task: TeachTask, call_tool: Callable[[str, dict], dict]) -> dict:
    """Execute the Teaching Agent flow: retrieve → multi-turn teach → connections → checklist → ingest."""
    max_turns = int(os.environ.get("EVO_TEACH_MAX_TURNS", "20"))

    # Step 1: Retrieve KB context
    query = task.artifact_slug or task.topic
    retrieve_out = call_tool("retrieve", {"query": query, "k": 8})
    kb_chunks = retrieve_out.get("results", [])
    context_text = "\n\n".join(
        f"[{r['title']}] {r['snippet']}" for r in kb_chunks
    ) or "No existing KB context."

    # Step 2: Generate opening (Layer 1)
    # TODO Phase D.1: pass TEACH_SYSTEM as system param once provider.chat() accepts system kwarg
    mastery_ctx = task.mastery_context or ""
    opening_prompt = (
        f"{TEACH_SYSTEM}\n\nTopic: {task.topic}\nKB context:\n{context_text}"
        + (f"\nLearner context: {mastery_ctx}" if mastery_ctx else "")
    )

    layer1_out = call_tool("generate", {
        "messages": [{"role": "user", "content": opening_prompt}],
        "context": kb_chunks,
    })

    session_log = [
        {"role": "assistant", "content": layer1_out.get("text", "")},
    ]

    # Step 3: Multi-turn teaching loop
    # Phase D CLI: 3 turns max for non-interactive mode.
    # Full interactive loop wired via POST /api/agent/[run_id]/message in T5.
    turn_count = 1
    while turn_count < min(3, max_turns):
        turn_out = call_tool("generate", {
            "messages": [{"role": "user", "content":
                TEACH_LAYER.format(
                    session_log=str(session_log),
                    user_response="[auto-advance: CLI mode]",
                )
            }],
            "context": kb_chunks,
        })
        session_log.append({"role": "assistant", "content": turn_out.get("text", "")})
        turn_count += 1

    # Step 4: Connections
    connections_out = call_tool("generate", {
        "messages": [{"role": "user", "content":
            TEACH_CONNECTIONS.format(session_log=str(session_log))
        }],
        "context": [],
    })
    session_log.append({"role": "assistant", "content": connections_out.get("text", "")})

    # Step 5: Mastery checklist
    checklist_out = call_tool("generate", {
        "messages": [{"role": "user", "content":
            TEACH_CHECKLIST.format(topic=task.topic, session_log=str(session_log))
        }],
        "context": [],
    })
    checklist_md = checklist_out.get("text", "")

    # Step 6: Ingest checklist artifact
    slug = re.sub(r"[^a-z0-9-]", "", f"{task.topic}-mastery-checklist".lower().replace(" ", "-"))[:60]
    checklist_html = (
        f"<html><body><h1>Mastery Checklist: {task.topic}</h1>"
        f"<pre>{checklist_md}</pre></body></html>"
    )

    ingest_out = call_tool("ingest", {
        "title": f"Mastery Checklist: {task.topic}",
        "slug": slug,
        "html_content": checklist_html,
        "summary": f"Mastery checklist for {task.topic} from teaching session.",
        "tags": [task.topic.lower(), "teaching", "mastery-checklist"],
    })

    return {
        "checklist_slug": ingest_out.get("slug", slug),
        "mastery_level": "partial",
        "concepts_connected": [],
    }
