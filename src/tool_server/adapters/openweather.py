"""OpenWeather adapter.

Encapsulates upstream API details and error normalization.
"""

from __future__ import annotations

import httpx

from . import AdapterError

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


def _raise_for_status(data: dict) -> None:
    cod = str(data.get("cod", ""))
    if cod and cod != "200":
        raise AdapterError("UPSTREAM_ERROR", data.get("message", "OpenWeather error"), {"code": cod})


def fetch_current_weather(
    *,
    api_key: str | None,
    city: str | None,
    lat: float | None,
    lon: float | None,
    units: str,
    lang: str | None,
    timeout_s: float,
) -> dict:
    if not api_key:
        raise AdapterError("MISSING_API_KEY", "OPENWEATHER_API_KEY is not set")

    params: dict[str, str | float] = {"appid": api_key, "units": units}
    if lang:
        params["lang"] = lang

    if city:
        params["q"] = city
    else:
        params["lat"] = lat or 0.0
        params["lon"] = lon or 0.0

    url = f"{OPENWEATHER_BASE_URL}/weather"
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url, params=params)
    data = resp.json()
    _raise_for_status(data)
    return data
