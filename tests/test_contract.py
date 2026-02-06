from agent_server.agent import build_openai_tools
from tool_server.tools import list_tool_specs


def test_tool_registry_matches_agent_specs():
    tool_names = {spec.name for spec in list_tool_specs()}
    openai_tools = build_openai_tools()
    openai_names = {tool["function"]["name"] for tool in openai_tools}
    assert tool_names == openai_names
