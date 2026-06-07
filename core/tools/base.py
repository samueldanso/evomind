"""Tool protocol and registry for the agent runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.governance.allowlist import AGENT_ALLOWLISTS, check_allowlist


@dataclass
class Tool:
    name: str
    description: str
    execute: Callable[[dict], dict]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            msg = f"Tool '{name}' is not registered"
            raise KeyError(msg)
        return self._tools[name]

    def build_for_agent(self, agent_type: str) -> dict[str, Tool]:
        """Return only the tools this agent is allowed to call."""
        allowed_names = AGENT_ALLOWLISTS.get(agent_type)
        if allowed_names is None:
            check_allowlist(agent_type, "")
        result: dict[str, Tool] = {}
        for name in allowed_names or []:
            if name in self._tools:
                result[name] = self._tools[name]
        return result
