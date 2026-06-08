"""Shared server utilities — request-scoped helpers."""

from __future__ import annotations

import sqlite3

from fastapi import Request

from core.llm.bedrock import BedrockProvider


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db


def get_provider(request: Request) -> BedrockProvider:
    return request.app.state.provider


def get_startup_error(request: Request) -> str | None:
    return getattr(request.app.state, "startup_error", None)
