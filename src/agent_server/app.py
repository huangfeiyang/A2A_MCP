"""FastAPI entry for the agent server."""

from __future__ import annotations

import uuid

import os

from fastapi import FastAPI, Request

from .executor import AskRequest, handle_ask
from .logging import get_logger
from .settings import get_settings

app = FastAPI(title="A2A Agent Server", version="0.1.0")
logger = get_logger("agent_server")


@app.on_event("startup")
def log_startup_config() -> None:
    settings = get_settings()
    logger.info(
        "agent_server_config",
        extra={
            "extra": {
                "openai_model": settings.openai_model,
                "mock_llm": settings.mock_llm,
                "mcp_base_url": settings.mcp_base_url,
                "openai_timeout_s": settings.openai_timeout_s,
                "env_mock_llm": os.environ.get("A2A_MCP_MOCK_LLM"),
                "env_mcp_base_url": os.environ.get("A2A_MCP_MCP_BASE_URL"),
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
        "name": "autocity-agent",
        "version": "0.1.0",
        "description": "Single agent demo with MCP tool server.",
        "endpoints": {"ask": "/v1/ask"},
        "mcp_base_url": settings.mcp_base_url,
    }


@app.post("/v1/ask")
async def ask(payload: AskRequest, request: Request):
    # Preserve incoming trace_id if provided, else generate one.
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    response = await handle_ask(payload, trace_id)
    return response
