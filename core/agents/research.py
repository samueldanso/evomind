"""Research Agent — step function for the agent execution loop."""

from __future__ import annotations

import re
from typing import Callable

from core.prompts.templates import RESEARCH_PRODUCE, RESEARCH_SYSTEM
from core.runtime.contracts import ResearchTask


def run_research_agent(task: ResearchTask, call_tool: Callable[[str, dict], dict]) -> dict:
    """Execute the Research Agent flow: retrieve → generate notes → produce HTML → ingest."""
    # Step 1: Retrieve existing KB context
    retrieve_out = call_tool("retrieve", {"query": task.topic, "k": 5})
    kb_chunks = retrieve_out.get("results", [])

    # Step 2: Generate research notes
    context_text = "\n\n".join(
        f"[{r['title']}] {r['snippet']}" for r in kb_chunks
    ) or "No existing KB context on this topic."

    # TODO Phase D.1: pass RESEARCH_SYSTEM as system param once provider.chat() accepts system kwarg
    user_prompt = f"{RESEARCH_SYSTEM}\n\nResearch topic: {task.topic}\nMode: {task.mode}"
    if task.context:
        user_prompt += f"\nAdditional context: {task.context}"
    user_prompt += f"\n\nExisting KB context:\n{context_text}"

    notes_out = call_tool("generate", {
        "messages": [{"role": "user", "content": user_prompt}],
        "context": kb_chunks,
    })
    notes = notes_out.get("text", "")

    # Step 3: Generate structured HTML artifact from notes
    artifact_out = call_tool("generate", {
        "messages": [
            {"role": "user", "content": f"Research notes:\n{notes}\n\n{RESEARCH_PRODUCE}"}
        ],
        "context": [],
    })
    html_content = artifact_out.get("text", "")

    # Step 4: Ingest artifact into KB
    slug = re.sub(r"[^a-z0-9-]", "", task.topic.lower().replace(" ", "-"))[:60]
    summary = notes[:500]

    ingest_out = call_tool("ingest", {
        "title": task.topic,
        "slug": slug,
        "html_content": html_content,
        "summary": summary,
        "tags": [task.topic.lower(), task.mode, "research"],
    })

    return {
        "artifact_slug": ingest_out.get("slug", slug),
        "artifact_id": ingest_out.get("artifact_id"),
        "summary": summary,
    }
