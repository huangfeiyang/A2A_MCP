"""FastAPI entry for the agent server."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request

from .executor import AskRequest, handle_ask
from .logging import get_logger
from .settings import get_settings

app = FastAPI(
    title=get_settings().service_title,
    version=get_settings().agent_version,
)
logger = get_logger("agent_server")


@app.on_event("startup")
def log_startup_config() -> None:
    settings = get_settings()
    logger.info(
        "agent_server_config",
        extra={
            "extra": {
                "agent_name": settings.agent_name,
                "agent_version": settings.agent_version,
                "openai_model": settings.openai_model,
                "openai_base_url": settings.openai_base_url,
                "temperature": settings.temperature,
                "max_tool_calls": settings.max_tool_calls,
                "tool_arg_retry_limit": settings.tool_arg_retry_limit,
                "mock_llm": settings.mock_llm,
                "host": settings.host,
                "port": settings.port,
                "mcp_base_url": settings.mcp_base_url,
                "openai_timeout_s": settings.openai_timeout_s,
                "request_timeout_s": settings.request_timeout_s,
                "trace_enabled": settings.trace_enabled,
                "trace_dir": settings.trace_dir,
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/agent-card")
def agent_card() -> dict[str, object]:
    settings = get_settings()
    return {
        "name": settings.agent_name,
        "version": settings.agent_version,
        "description": settings.agent_description,
        "endpoints": {"ask": "/v1/ask"},
        "mcp_base_url": settings.mcp_base_url,
    }


@app.post("/v1/ask")
async def ask(payload: AskRequest, request: Request):
    # Preserve incoming trace_id if provided, else generate one.
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    response = await handle_ask(payload, trace_id)
    return response
