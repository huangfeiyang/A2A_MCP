"""Unified tool calling layer.

This isolates tool invocation details (HTTP/in-proc, retries, errors)
from the agent reasoning logic.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from tool_server.schemas import ToolError, ToolMeta, ToolResponse
from tool_server.tools import get_tool_handler, get_tool_spec
from .logging import get_logger
from .settings import AgentSettings
from .trace import record_tool_call

logger = get_logger("tool_broker")


class ToolBroker:
    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings

    async def call_tool(
        self,
        name: str,
        args: dict[str, Any],
        trace_id: str,
        trace: object | None = None,
    ) -> ToolResponse:
        # Allow in-process calls for tests or local debugging.
        if self._settings.mcp_base_url == "inproc":
            return self._call_tool_inproc(name, args, trace_id, trace)
        return await self._call_tool_http(name, args, trace_id, trace)

    def _call_tool_inproc(
        self,
        name: str,
        args: dict[str, Any],
        trace_id: str,
        trace: object | None = None,
    ) -> ToolResponse:
        # Local in-process handler avoids HTTP overhead.
        start = time.time()
        spec = get_tool_spec(name)
        handler = get_tool_handler(name)
        if not spec or not handler:
            return ToolResponse(
                ok=False,
                data=None,
                error=ToolError(code="NOT_FOUND", message=f"Unknown tool: {name}"),
                meta=ToolMeta(tool_name=name, trace_id=trace_id),
            )
        try:
            input_obj = spec.input_model.model_validate(args)
            result = handler(input_obj, _inproc_settings(), trace_id)
            latency_ms = int((time.time() - start) * 1000)
            response = ToolResponse(
                ok=True,
                data=result.model_dump(),
                error=None,
                meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=latency_ms),
            )
            if trace is not None:
                record_tool_call(
                    trace,
                    tool_name=name,
                    args=args,
                    ok=True,
                    latency_ms=latency_ms,
                    result=response.data,
                    error=None,
                )
            return response
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.time() - start) * 1000)
            response = ToolResponse(
                ok=False,
                data=None,
                error=ToolError(code="TOOL_ERROR", message=str(exc)),
                meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=latency_ms),
            )
            if trace is not None:
                record_tool_call(
                    trace,
                    tool_name=name,
                    args=args,
                    ok=False,
                    latency_ms=latency_ms,
                    result=None,
                    error=response.error.model_dump() if response.error else None,
                )
            return response

    async def _call_tool_http(
        self,
        name: str,
        args: dict[str, Any],
        trace_id: str,
        trace: object | None = None,
    ) -> ToolResponse:
        # Standard path: HTTP request to tool server.
        url = f"{self._settings.mcp_base_url}/tools/{name}"
        start = time.time()
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.request_timeout_s, trust_env=False
            ) as client:
                resp = await client.post(url, json=args, headers={"x-trace-id": trace_id})
        except httpx.RequestError as exc:
            latency_ms = int((time.time() - start) * 1000)
            logger.info(
                "tool_call_failed",
                extra={
                    "extra": {
                        "trace_id": trace_id,
                        "tool": name,
                        "latency_ms": latency_ms,
                        "error": str(exc),
                    }
                },
            )
            response = ToolResponse(
                ok=False,
                data=None,
                error=ToolError(code="TOOL_UNAVAILABLE", message=str(exc)),
                meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=latency_ms),
            )
            if trace is not None:
                record_tool_call(
                    trace,
                    tool_name=name,
                    args=args,
                    ok=False,
                    latency_ms=latency_ms,
                    result=None,
                    error=response.error.model_dump() if response.error else None,
                )
            return response
        latency_ms = int((time.time() - start) * 1000)
        if resp.status_code >= 500:
            response = ToolResponse(
                ok=False,
                data=None,
                error=ToolError(
                    code="TOOL_UPSTREAM_5XX",
                    message=f"Tool server error: {resp.status_code}",
                ),
                meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=latency_ms),
            )
            if trace is not None:
                record_tool_call(
                    trace,
                    tool_name=name,
                    args=args,
                    ok=False,
                    latency_ms=latency_ms,
                    result=None,
                    error=response.error.model_dump() if response.error else None,
                )
            return response

        try:
            data = resp.json()
        except ValueError as exc:
            response = ToolResponse(
                ok=False,
                data=None,
                error=ToolError(code="TOOL_BAD_RESPONSE", message=str(exc)),
                meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=latency_ms),
            )
            if trace is not None:
                record_tool_call(
                    trace,
                    tool_name=name,
                    args=args,
                    ok=False,
                    latency_ms=latency_ms,
                    result=None,
                    error=response.error.model_dump() if response.error else None,
                )
            return response

        logger.info(
            "tool_call",
            extra={
                "extra": {
                    "trace_id": trace_id,
                    "tool": name,
                    "latency_ms": latency_ms,
                    "status_code": resp.status_code,
                }
            },
        )

        response = ToolResponse.model_validate(data)
        if trace is not None:
            record_tool_call(
                trace,
                tool_name=name,
                args=args,
                ok=response.ok,
                latency_ms=latency_ms,
                result=response.data if response.ok else None,
                error=response.error.model_dump() if response.error else None,
            )
        return response


def _inproc_settings():
    from tool_server.settings import get_settings

    return get_settings()
