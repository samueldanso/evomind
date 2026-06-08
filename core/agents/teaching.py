"""Teaching Agent — step function for the agent execution loop."""

from __future__ import annotations

import os
import re
from typing import Callable

from core.prompts.templates import TEACH_CHECKLIST, TEACH_CONNECTIONS, TEACH_LAYER, TEACH_SYSTEM
from core.runtime.contracts import TeachTask


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
