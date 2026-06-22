#!/usr/bin/env python3
"""CLI dispatch for Evo agents.

Usage:
    uv run scripts/agent.py --task research --topic "KV Cache" --mode concept
    uv run scripts/agent.py --task teach --topic "KV Cache"
    uv run scripts/agent.py --task research --topic "vLLM" --mode tool --no-auto-teach
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm.bedrock import get_provider
from core.memory.db import open_db
from core.runtime.contracts import ResearchTask, TeachTask
from core.runtime.dispatcher import dispatch


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evo agent CLI")
    parser.add_argument("--task", choices=["research", "teach"], required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--mode", choices=["concept", "tool", "company"], default="concept")
    parser.add_argument("--no-auto-teach", action="store_true")
    parser.add_argument("--context", default=None)
    args = parser.parse_args(argv)

    db = open_db()
    provider = get_provider()

    if args.task == "research":
        task = ResearchTask(
            task_type="research",
            topic=args.topic,
            mode=args.mode,
            context=args.context,
        )
        result = dispatch(task, db, provider, auto_teach=not args.no_auto_teach)
    else:
        task = TeachTask(
            task_type="teach",
            topic=args.topic,
        )
        result = dispatch(task, db, provider)

    if isinstance(result, tuple):
        research_run, teach_run = result
        print(
            f"Research: status={research_run.status} "
            f"slug={research_run.output.get('artifact_slug') if research_run.output else None} "
            f"cost=${research_run.cost_usd:.4f}"
        )
        print(
            f"Teaching: status={teach_run.status} "
            f"slug={teach_run.output.get('checklist_slug') if teach_run.output else None} "
            f"cost=${teach_run.cost_usd:.4f}"
        )
    else:
        run = result
        print(f"{run.agent_type}: status={run.status} cost=${run.cost_usd:.4f}")
        if run.output:
            print(f"Output: {run.output}")
        if run.error:
            print(f"Error: {run.error}", file=sys.stderr)

    db.close()


if __name__ == "__main__":
    main()
