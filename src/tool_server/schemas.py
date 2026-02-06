"""Shared tool schemas (single source of truth).

Agent and tool server should both import these models to avoid drift.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ToolError(BaseModel):
    """Normalized error payload returned by tools."""
    code: str
    message: str
    details: dict[str, Any] | None = None


class ToolMeta(BaseModel):
    """Metadata attached to tool responses for observability."""
    tool_name: str
    trace_id: str
    latency_ms: int | None = None
    source: str | None = None


class ToolResponse(BaseModel):
    """Unified response wrapper for all tools."""
    ok: bool
    data: Any | None = None
    error: ToolError | None = None
    meta: ToolMeta


class TimeInput(BaseModel):
    """Input for time tool."""
    timezone: str | None = Field(default=None, description="IANA timezone string")


class TimeOutput(BaseModel):
    """Output for time tool."""
    timezone: str
    iso: str
    epoch_seconds: int


class WeatherInput(BaseModel):
    """Input for weather tool."""
    city: str | None = Field(default=None, description="City name, e.g. Beijing")
    lat: float | None = Field(default=None, description="Latitude")
    lon: float | None = Field(default=None, description="Longitude")
    units: Literal["metric", "imperial"] = "metric"
    lang: str | None = Field(default=None, description="Response language")

    @model_validator(mode="after")
    def _validate_location(self) -> "WeatherInput":
        has_city = bool(self.city and self.city.strip())
        has_coords = self.lat is not None and self.lon is not None
        if not (has_city or has_coords):
            raise ValueError("Provide either city or (lat, lon).")
        return self


class WeatherOutput(BaseModel):
    """Output for weather tool."""
    source: str
    city: str | None = None
    lat: float | None = None
    lon: float | None = None
    description: str | None = None
    temperature_c: float | None = None
    feels_like_c: float | None = None
    humidity: int | None = None
    wind_speed: float | None = None
    observation_time: str | None = None


class PoiInput(BaseModel):
    """Input for POI tool."""
    city: str | None = Field(default=None, description="City name")
    lat: float | None = Field(default=None, description="Latitude")
    lon: float | None = Field(default=None, description="Longitude")
    keyword: str | None = Field(default=None, description="Search keyword")
    types: str | None = Field(default=None, description="AMap POI types")
    radius_m: int = Field(default=2000, ge=100, le=50000)
    limit: int = Field(default=10, ge=1, le=50)
    lang: str | None = Field(default=None, description="Response language")

    @model_validator(mode="after")
    def _validate_location(self) -> "PoiInput":
        has_city = bool(self.city and self.city.strip())
        has_coords = self.lat is not None and self.lon is not None
        if not (has_city or has_coords):
            raise ValueError("Provide either city or (lat, lon).")
        return self


class PoiItem(BaseModel):
    """Single POI item."""
    name: str
    address: str | None = None
    lat: float
    lon: float
    distance_m: int | None = None


class PoiOutput(BaseModel):
    """Output for POI tool."""
    city: str | None = None
    keyword: str | None = None
    items: list[PoiItem]


@dataclass(frozen=True)
class ToolSpec:
    """Tool registry metadata used by agent/tool server."""
    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
