"""Tests for core/runtime/contracts.py — typed task contracts."""

import pytest

from core.runtime.contracts import ResearchTask, TeachTask, validate_task


class TestResearchTask:
    def test_valid_research_task_concept(self):
        task = ResearchTask(task_type="research", topic="KV Cache", mode="concept")
        validate_task(task)

    def test_valid_research_task_tool(self):
        task = ResearchTask(task_type="research", topic="vLLM", mode="tool")
        validate_task(task)

    def test_valid_research_task_company(self):
        task = ResearchTask(task_type="research", topic="Anthropic", mode="company")
        validate_task(task)

    def test_research_missing_topic(self):
        task = ResearchTask(task_type="research", topic="", mode="concept")
        with pytest.raises(ValueError, match="non-empty"):
            validate_task(task)

    def test_research_invalid_mode(self):
        task = ResearchTask(task_type="research", topic="KV Cache", mode="invalid")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="must be one of"):
            validate_task(task)


class TestTeachTask:
    def test_valid_teach_task(self):
        task = TeachTask(task_type="teach", topic="KV Cache")
        validate_task(task)

    def test_valid_teach_task_with_slug(self):
        task = TeachTask(task_type="teach", topic="KV Cache", artifact_slug="kv-cache")
        validate_task(task)

    def test_teach_missing_topic(self):
        task = TeachTask(task_type="teach", topic="")
        with pytest.raises(ValueError, match="non-empty"):
            validate_task(task)
