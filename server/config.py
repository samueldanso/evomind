"""Server configuration — environment variables and startup validation."""

from __future__ import annotations

import os

EVO_CHAT_PORT = int(os.environ.get("EVO_CHAT_PORT", "8765"))
EVO_TEACH_MAX_TURNS = int(os.environ.get("EVO_TEACH_MAX_TURNS", "20"))
EVO_RESEARCH_STORE = os.environ.get("EVO_RESEARCH_STORE")
