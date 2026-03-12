from agent_server.settings import get_settings as get_agent_settings
from client.settings import get_settings as get_client_settings
from tool_server.settings import get_settings as get_tool_settings


def _clear_settings_cache() -> None:
    get_agent_settings.cache_clear()
    get_tool_settings.cache_clear()
    get_client_settings.cache_clear()


def test_agent_settings_read_explicit_openai_and_metadata_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("A2A_MCP_AGENT_NAME", "demo-agent")
    monkeypatch.setenv("A2A_MCP_AGENT_PORT", "7010")

    _clear_settings_cache()

    settings = get_agent_settings()

    assert settings.openai_api_key == "sk-test"
    assert settings.openai_base_url == "https://example.com/v1"
    assert settings.agent_name == "demo-agent"
    assert settings.port == 7010


def test_tool_and_client_settings_use_service_specific_env(monkeypatch):
    monkeypatch.setenv("A2A_MCP_TOOL_PORT", "7011")
    monkeypatch.setenv("A2A_MCP_TOOL_DEFAULT_LANG", "en")
    monkeypatch.setenv("A2A_MCP_AGENT_BASE_URL", "http://localhost:7010")

    _clear_settings_cache()

    tool_settings = get_tool_settings()
    client_settings = get_client_settings()

    assert tool_settings.port == 7011
    assert tool_settings.default_lang == "en"
    assert client_settings.agent_base_url == "http://localhost:7010"
