"""Trace recording utilities for end-to-end request replay."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .state import TraceRecord


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_trace(trace_id: str, query: str, client_meta: dict[str, Any] | None = None) -> TraceRecord:
    trace = TraceRecord(trace_id=trace_id, started_at=now_utc_iso())
    trace.request = {
        "user_query": query,
        "client_meta": client_meta or {},
    }
    return trace


def record_llm_call(
    trace: TraceRecord,
    *,
    model: str,
    temperature: float,
    tool_calls: list[dict[str, Any]],
    messages_summary: list[dict[str, Any]] | None = None,
    finish_reason: str | None = None,
) -> None:
    trace.llm.append(
        {
            "model": model,
            "temperature": temperature,
            "messages_summary": messages_summary or [],
            "tool_calls": tool_calls,
            "finish_reason": finish_reason,
        }
    )


def record_tool_call(
    trace: TraceRecord,
    *,
    tool_name: str,
    args: dict[str, Any],
    ok: bool,
    latency_ms: int | None,
    result: dict[str, Any] | None,
    error: dict[str, Any] | None,
) -> None:
    trace.tools.append(
        {
            "tool_name": tool_name,
            "args": args,
            "status": "ok" if ok else "error",
            "latency_ms": latency_ms,
            "result": result,
            "error": error,
        }
    )


def record_final(trace: TraceRecord, answer_text: str, render_meta: dict[str, Any] | None = None) -> None:
    trace.final = {
        "answer_text": answer_text,
        "render_meta": render_meta or {},
    }


def finalize_trace(trace: TraceRecord, started_at_ts: float) -> None:
    trace.finished_at = now_utc_iso()
    trace.latency_ms = int((time.time() - started_at_ts) * 1000)


def write_trace(trace: TraceRecord, trace_dir: str) -> Path:
    os.makedirs(trace_dir, exist_ok=True)
    ts = trace.started_at.replace(":", "-")
    filename = f"{ts}_{trace.trace_id}.json"
    path = Path(trace_dir) / filename
    path.write_text(json.dumps(asdict(trace), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
