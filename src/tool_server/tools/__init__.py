"""Tool registry for the MCP tool server."""

from __future__ import annotations

from typing import Callable

from ..schemas import (
    PoiInput,
    PoiOutput,
    TimeInput,
    TimeOutput,
    ToolSpec,
    WeatherInput,
    WeatherOutput,
)
from .poi import search_poi
from .time import get_current_time
from .weather import get_weather

ToolHandler = Callable[[object, object, str], object]

TOOL_SPECS: dict[str, ToolSpec] = {
    "time": ToolSpec(
        name="time",
        description=(
            "Get the current time. Use this for time/date questions. "
            "Optional argument: `timezone` as an IANA timezone string such as `Asia/Shanghai` or "
            "`UTC`. If the user does not specify a timezone, omit `timezone`."
        ),
        input_model=TimeInput,
        output_model=TimeOutput,
    ),
    "weather": ToolSpec(
        name="weather",
        description=(
            "Get current weather. You must provide either `city` or both `lat` and `lon`. "
            "When the user mentions a city, pass it in `city`. "
            "Do not call this tool with only optional fields such as `units` or `lang`."
        ),
        input_model=WeatherInput,
        output_model=WeatherOutput,
    ),
    "poi": ToolSpec(
        name="poi",
        description=(
            "Search nearby points of interest. You must provide either `city` or both `lat` and "
            "`lon`. Also provide a useful `keyword` that matches user intent, for example 景点, "
            "餐厅, 博物馆, 咖啡."
        ),
        input_model=PoiInput,
        output_model=PoiOutput,
    ),
}

TOOL_HANDLERS: dict[str, ToolHandler] = {
    "time": get_current_time,
    "weather": get_weather,
    "poi": search_poi,
}


def get_tool_spec(name: str) -> ToolSpec | None:
    return TOOL_SPECS.get(name)


def get_tool_handler(name: str) -> ToolHandler | None:
    return TOOL_HANDLERS.get(name)


def list_tool_specs() -> list[ToolSpec]:
    return list(TOOL_SPECS.values())
