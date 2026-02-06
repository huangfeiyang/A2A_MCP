"""FastAPI app for MCP-style tool server.

This server exposes a small set of tools with structured I/O.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from .logging import get_logger
from .adapters import AdapterError
from .schemas import ToolError, ToolMeta, ToolResponse
from .settings import get_settings
from .tools import get_tool_handler, get_tool_spec, list_tool_specs

logger = get_logger("tool_server")

app = FastAPI(title="A2A MCP Tool Server", version="0.1.0")


@app.on_event("startup")
def log_startup_config() -> None:
    settings = get_settings()
    logger.info(
        "tool_server_config",
        extra={
            "extra": {
                "openweather_key_set": bool(settings.openweather_api_key),
                "amap_key_set": bool(settings.amap_api_key),
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.input_model.model_json_schema(),
            "output_schema": spec.output_model.model_json_schema(),
        }
        for spec in list_tool_specs()
    ]


@app.post("/tools/{tool_name}")
async def call_tool(tool_name: str, request: Request) -> ToolResponse:
    # Every tool call gets a trace_id for end-to-end debugging.
    trace_id = request.headers.get("x-trace-id") or str(uuid.uuid4())
    start = time.time()
    settings = get_settings()

    spec = get_tool_spec(tool_name)
    handler = get_tool_handler(tool_name)
    if not spec or not handler:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

    try:
        payload = await request.json()
        input_obj = spec.input_model.model_validate(payload)
        result = handler(input_obj, settings, trace_id)
        latency_ms = int((time.time() - start) * 1000)
        response = ToolResponse(
            ok=True,
            data=result.model_dump(),
            error=None,
            meta=ToolMeta(tool_name=tool_name, trace_id=trace_id, latency_ms=latency_ms),
        )
        logger.info(
            "tool_call",
            extra={
                "extra": {
                    "trace_id": trace_id,
                    "tool": tool_name,
                    "latency_ms": latency_ms,
                    "ok": True,
                }
            },
        )
        return response
    except ValidationError as exc:
        latency_ms = int((time.time() - start) * 1000)
        error = ToolError(code="INVALID_ARGUMENT", message=str(exc))
        logger.info(
            "tool_validation_error",
            extra={
                "extra": {
                    "trace_id": trace_id,
                    "tool": tool_name,
                    "latency_ms": latency_ms,
                    "ok": False,
                    "error_code": error.code,
                }
            },
        )
        return ToolResponse(
            ok=False,
            data=None,
            error=error,
            meta=ToolMeta(tool_name=tool_name, trace_id=trace_id, latency_ms=latency_ms),
        )
    except AdapterError as exc:
        latency_ms = int((time.time() - start) * 1000)
        error = ToolError(code=exc.code, message=exc.message, details=exc.details)
        logger.info(
            "tool_adapter_error",
            extra={
                "extra": {
                    "trace_id": trace_id,
                    "tool": tool_name,
                    "latency_ms": latency_ms,
                    "ok": False,
                    "error_code": error.code,
                }
            },
        )
        return ToolResponse(
            ok=False,
            data=None,
            error=error,
            meta=ToolMeta(tool_name=tool_name, trace_id=trace_id, latency_ms=latency_ms),
        )
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.time() - start) * 1000)
        error = ToolError(code="TOOL_ERROR", message=str(exc))
        logger.info(
            "tool_error",
            extra={
                "extra": {
                    "trace_id": trace_id,
                    "tool": tool_name,
                    "latency_ms": latency_ms,
                    "ok": False,
                    "error_code": error.code,
                }
            },
        )
        return ToolResponse(
            ok=False,
            data=None,
            error=error,
            meta=ToolMeta(tool_name=tool_name, trace_id=trace_id, latency_ms=latency_ms),
        )


def main() -> None:
    import uvicorn

    from .settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "tool_server.server:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
