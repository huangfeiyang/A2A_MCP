import os

from fastapi.testclient import TestClient

from agent_server import app as agent_app
from agent_server.settings import get_settings as get_agent_settings
from tool_server.settings import get_settings as get_tool_settings


def test_smoke_ask_with_mock(monkeypatch):
    monkeypatch.setenv("A2A_MCP_MOCK_LLM", "true")
    monkeypatch.setenv("A2A_MCP_MCP_BASE_URL", "inproc")

    # Clear cached settings so env takes effect
    get_agent_settings.cache_clear()
    get_tool_settings.cache_clear()

    client = TestClient(agent_app.app)
    resp = client.post("/v1/ask", json={"query": "现在几点了？"})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "trace_id" in data
