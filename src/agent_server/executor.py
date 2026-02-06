"""Protocol adapter for incoming requests.

Keep this layer thin so protocol changes do not affect core agent logic.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

from .agent import Agent
from .settings import get_settings
from .trace import build_trace, finalize_trace, record_final, write_trace


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)
    conversation_id: str | None = None


class AskResponse(BaseModel):
    answer: str
    trace_id: str
    tool_calls: list[dict] | None = None


async def handle_ask(payload: AskRequest, trace_id: str) -> AskResponse:
    # Construct agent per request for simplicity; can be cached later.
    settings = get_settings()
    agent = Agent(settings)
    started_at_ts = time.time()
    trace = build_trace(trace_id, payload.query)
    state = await agent.run(payload.query, trace_id, trace)

    tool_calls = [
        {
            "name": call.name,
            "arguments": call.arguments,
            "ok": call.ok,
            "output": call.output,
            "error": call.error,
        }
        for call in state.tool_calls
    ]

    answer = state.final_answer or ""
    record_final(trace, answer_text=answer)
    finalize_trace(trace, started_at_ts)
    if settings.trace_enabled:
        write_trace(trace, settings.trace_dir)

    return AskResponse(answer=answer, trace_id=trace_id, tool_calls=tool_calls)
