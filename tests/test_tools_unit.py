from tool_server.settings import ToolServerSettings
from tool_server.schemas import TimeInput
from tool_server.tools.time import get_current_time


def test_time_tool_basic():
    settings = ToolServerSettings()
    payload = TimeInput(timezone="UTC")
    result = get_current_time(payload, settings, "trace")
    assert result.timezone == "UTC"
    assert "T" in result.iso
    assert result.epoch_seconds > 0
