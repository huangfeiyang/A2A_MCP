from agent_server.agent import build_openai_tools
from tool_server.tools import list_tool_specs


def test_tool_registry_matches_agent_specs():
    tool_names = {spec.name for spec in list_tool_specs()}
    openai_tools = build_openai_tools()
    openai_names = {tool["function"]["name"] for tool in openai_tools}
    assert tool_names == openai_names


def test_tool_descriptions_preserve_key_argument_rules():
    openai_tools = build_openai_tools()
    descriptions = {tool["function"]["name"]: tool["function"]["description"] for tool in openai_tools}

    assert "either `city` or both `lat` and `lon`" in descriptions["weather"]
    assert "Do not call this tool with only optional fields" in descriptions["weather"]
    assert "provide a useful `keyword`" in descriptions["poi"]
