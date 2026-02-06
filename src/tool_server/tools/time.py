"""Time tool (no external dependency)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from ..schemas import TimeInput, TimeOutput
from ..settings import ToolServerSettings


def get_current_time(payload: TimeInput, settings: ToolServerSettings, _trace_id: str) -> TimeOutput:
    # Resolve timezone from input or default setting.
    tz_name = payload.timezone or settings.default_timezone
    if tz_name.upper() == "UTC":
        tz = timezone.utc
    else:
        tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    return TimeOutput(
        timezone=tz_name,
        iso=now.isoformat(),
        epoch_seconds=int(now.timestamp()),
    )
