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
        description="Get the current time for a timezone.",
        input_model=TimeInput,
        output_model=TimeOutput,
    ),
    "weather": ToolSpec(
        name="weather",
        description="Get current weather by city or coordinates.",
        input_model=WeatherInput,
        output_model=WeatherOutput,
    ),
    "poi": ToolSpec(
        name="poi",
        description="Search nearby points of interest.",
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
