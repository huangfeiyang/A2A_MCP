"""Lightweight request state container."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TraceRecord:
    """Structured trace container for a single request."""

    trace_id: str
    started_at: str
    finished_at: str | None = None
    latency_ms: int | None = None
    request: dict[str, Any] = field(default_factory=dict)
    llm: list[dict[str, Any]] = field(default_factory=list)
    tools: list[dict[str, Any]] = field(default_factory=list)
    final: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallRecord:
    name: str
    arguments: dict[str, Any]
    ok: bool
    output: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


@dataclass
class AgentState:
    query: str
    trace_id: str
    trace: TraceRecord
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    observations: list[dict[str, Any]] = field(default_factory=list)
    final_answer: str | None = None
