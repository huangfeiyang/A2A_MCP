import asyncio
import json
from types import SimpleNamespace

from agent_server.agent import Agent
from agent_server.settings import AgentSettings
from agent_server.trace import build_trace
from tool_server.schemas import ToolError, ToolMeta, ToolResponse


class FakeCompletions:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


class FakeBroker:
    def __init__(self):
        self.calls = []

    async def call_tool(self, name, args, trace_id, trace):
        self.calls.append((name, args))
        if len(self.calls) == 1:
            return ToolResponse(
                ok=False,
                data=None,
                error=ToolError(
                    code="INVALID_ARGUMENT",
                    message="Provide either city or (lat, lon).",
                ),
                meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=1),
            )

        return ToolResponse(
            ok=True,
            data={
                "source": "openweather",
                "city": "Beijing",
                "description": "晴",
                "temperature_c": 21.0,
            },
            error=None,
            meta=ToolMeta(tool_name=name, trace_id=trace_id, latency_ms=1),
        )


def _response(tool_calls, finish_reason="tool_calls", content=""):
    tool_call_objects = []
    for idx, (name, args) in enumerate(tool_calls, start=1):
        tool_call_objects.append(
            SimpleNamespace(
                id=f"call_{idx}",
                function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
            )
        )

    message = SimpleNamespace(content=content, tool_calls=tool_call_objects)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice])


def test_agent_retries_invalid_tool_args_with_forced_tool_choice():
    settings = AgentSettings(max_tool_calls=3, tool_arg_retry_limit=1)
    agent = Agent(settings)
    fake_client = FakeClient(
        [
            _response([("weather", {"units": "metric"})]),
            _response([("weather", {"city": "北京", "units": "metric"})]),
            _response([], finish_reason="stop"),
            _response([], finish_reason="stop", content="北京天气晴，21°C。"),
        ]
    )
    fake_broker = FakeBroker()
    agent._client = fake_client
    agent._broker = fake_broker

    trace = build_trace("trace-1", "北京今天天气怎么样？")
    state = asyncio.run(agent.run("北京今天天气怎么样？", "trace-1", trace))

    assert fake_broker.calls == [
        ("weather", {"units": "metric"}),
        ("weather", {"city": "北京", "units": "metric"}),
    ]
    assert fake_client.chat.completions.calls[0]["tool_choice"] == "auto"
    assert fake_client.chat.completions.calls[1]["tool_choice"] == {
        "type": "function",
        "function": {"name": "weather"},
    }
    assert state.tool_calls[0].ok is False
    assert state.tool_calls[1].ok is True
    assert state.final_answer == "北京天气晴，21°C。"
