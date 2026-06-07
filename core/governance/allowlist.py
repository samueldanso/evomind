"""Per-agent tool allowlist enforcement."""

from __future__ import annotations

AGENT_ALLOWLISTS: dict[str, list[str]] = {
    "research_agent": ["retrieve", "generate", "ingest"],
    "teaching_agent": ["retrieve", "generate", "ingest"],
}


def check_allowlist(agent_type: str, tool_name: str) -> None:
    """Raise PermissionError if tool_name is not allowed for agent_type."""
    if agent_type not in AGENT_ALLOWLISTS:
        msg = f"Unknown agent type: '{agent_type}'"
        raise PermissionError(msg)
    allowed = AGENT_ALLOWLISTS[agent_type]
    if tool_name not in allowed:
        msg = f"Agent '{agent_type}' is not allowed to call tool '{tool_name}'. Allowed: {allowed}"
        raise PermissionError(msg)
