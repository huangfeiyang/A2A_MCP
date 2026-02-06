"""Single-agent tool-use loop.

Design goals:
- Keep tool execution out of the LLM prompt by returning structured data.
- Make the flow testable by supporting a mock LLM path.
"""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from tool_server.tools import list_tool_specs
from .logging import get_logger
from .prompts import PLANNER_SYSTEM, RESPONDER_SYSTEM
from .settings import AgentSettings
from .state import AgentState, ToolCallRecord, TraceRecord
from .trace import record_llm_call
from .tool_broker import ToolBroker

logger = get_logger("agent")


def build_openai_tools() -> list[dict[str, Any]]:
    """Translate internal tool specs into OpenAI tool schema."""
    tools: list[dict[str, Any]] = []
    for spec in list_tool_specs():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.input_model.model_json_schema(),
                },
            }
        )
    return tools


class Agent:
    def __init__(self, settings: AgentSettings) -> None:
        self._settings = settings
        self._broker = ToolBroker(settings)
        self._client = None
        if settings.openai_api_key:
            self._client = OpenAI(api_key=settings.openai_api_key)

    async def run(self, query: str, trace_id: str, trace: TraceRecord) -> AgentState:
        """Run a single request through the tool-use loop."""
        state = AgentState(query=query, trace_id=trace_id, trace=trace)
        if self._settings.mock_llm or not self._client:
            return await self._run_mock(state)

        tools = build_openai_tools()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": query},
        ]
        remaining = self._settings.max_tool_calls

        while True:
            try:
                response = self._client.chat.completions.create(
                    model=self._settings.openai_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=self._settings.temperature,
                    timeout=self._settings.openai_timeout_s,
                )
                message = response.choices[0].message
                record_llm_call(
                    trace,
                    model=self._settings.openai_model,
                    temperature=self._settings.temperature,
                    tool_calls=_summarize_tool_calls(message),
                    messages_summary=_summarize_messages(messages),
                    finish_reason=response.choices[0].finish_reason,
                )
            except Exception as exc:  # noqa: BLE001
                logger.info(
                    "llm_error",
                    extra={"extra": {"trace_id": trace_id, "error": str(exc)}},
                )
                state.final_answer = "LLM 调用失败，请检查配置。"
                return state

            if not message.tool_calls:
                break

            # Add the assistant tool-call message so the tool responses are valid.
            messages.append(_assistant_tool_call_message(message))

            # Execute tool calls sequentially (kept simple for clarity).
            for call in message.tool_calls:
                if remaining <= 0:
                    break
                tool_name = call.function.name
                args = json.loads(call.function.arguments or "{}")
                result = await self._broker.call_tool(tool_name, args, trace_id, trace)
                state.tool_calls.append(
                    ToolCallRecord(
                        name=tool_name,
                        arguments=args,
                        ok=result.ok,
                        output=result.data if result.ok else None,
                        error=result.error.model_dump() if result.error else None,
                    )
                )
                tool_payload = result.data if result.ok else {"error": result.error.model_dump()}
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": tool_name,
                        "content": json.dumps(tool_payload, ensure_ascii=False),
                    }
                )
                remaining -= 1

            if remaining <= 0:
                break

        # Final response uses tool observations as context.
        final_messages = [{"role": "system", "content": RESPONDER_SYSTEM}] + messages[1:]
        try:
            final = self._client.chat.completions.create(
                model=self._settings.openai_model,
                messages=final_messages,
                temperature=self._settings.temperature,
                timeout=self._settings.openai_timeout_s,
            )
            record_llm_call(
                trace,
                model=self._settings.openai_model,
                temperature=self._settings.temperature,
                tool_calls=[],
                messages_summary=_summarize_messages(final_messages),
                finish_reason=final.choices[0].finish_reason,
            )
            state.final_answer = final.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            logger.info(
                "llm_error",
                extra={"extra": {"trace_id": trace_id, "error": str(exc)}},
            )
            state.final_answer = "LLM 调用失败，请检查配置。"

        return state

    async def _run_mock(self, state: AgentState) -> AgentState:
        """Heuristic mock mode: enables E2E flow without external LLM."""
        query = state.query
        tools_to_call: list[tuple[str, dict[str, Any]]] = []

        if re.search(r"时间|time", query, re.IGNORECASE):
            tools_to_call.append(("time", {}))
        elif re.search(r"天气|weather", query, re.IGNORECASE):
            city = _extract_city(query) or "Beijing"
            tools_to_call.append(("weather", {"city": city}))
        elif re.search(r"附近|poi|景点|餐厅", query, re.IGNORECASE):
            city = _extract_city(query) or "Beijing"
            tools_to_call.append(("poi", {"city": city, "keyword": "景点"}))

        if not tools_to_call:
            state.final_answer = "我可以帮你查时间、天气或附近 POI。请告诉我具体需求。"
            return state

        for name, args in tools_to_call[: self._settings.max_tool_calls]:
            result = await self._broker.call_tool(name, args, state.trace_id, state.trace)
            state.tool_calls.append(
                ToolCallRecord(
                    name=name,
                    arguments=args,
                    ok=result.ok,
                    output=result.data if result.ok else None,
                    error=result.error.model_dump() if result.error else None,
                )
            )

        if state.tool_calls and state.tool_calls[0].ok:
            payload = state.tool_calls[0].output or {}
            if tools_to_call[0][0] == "time":
                state.final_answer = f"当前时间：{payload.get('iso')} ({payload.get('timezone')})"
            elif tools_to_call[0][0] == "weather":
                city_name = payload.get("city") or "目标城市"
                state.final_answer = (
                    f"{city_name}天气：{payload.get('description')}，温度 {payload.get('temperature_c')}°C"
                )
            else:
                items = payload.get("items", [])
                top = items[0]["name"] if items else "暂无结果"
                state.final_answer = f"附近推荐：{top}"
        else:
            state.final_answer = "工具调用失败，请检查工具服务或 API Key。"

        return state


def _extract_city(text: str) -> str | None:
    match = re.search(r"(北京|上海|广州|深圳|杭州|成都)", text)
    return match.group(1) if match else None


def _summarize_tool_calls(message: Any) -> list[dict[str, Any]]:
    tool_calls_summary: list[dict[str, Any]] = []
    if message.tool_calls:
        for call in message.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            tool_calls_summary.append({"name": call.function.name, "args": args})
    return tool_calls_summary


def _summarize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"role": msg.get("role"), "content_len": len(str(msg.get("content", "")))}
        for msg in messages
    ]


def _assistant_tool_call_message(message: Any) -> dict[str, Any]:
    tool_calls_payload = []
    for call in message.tool_calls:
        tool_calls_payload.append(
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
        )
    return {
        "role": "assistant",
        "content": message.content or "",
        "tool_calls": tool_calls_payload,
    }
