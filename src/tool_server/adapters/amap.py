"""AMap (Gaode) adapter.

Encapsulates upstream API details and error normalization.
"""

from __future__ import annotations

import httpx

from . import AdapterError

AMAP_BASE_URL = "https://restapi.amap.com/v3"


def _raise_for_status(data: dict) -> None:
    if str(data.get("status")) != "1":
        raise AdapterError("UPSTREAM_ERROR", data.get("info", "AMap error"), {"infocode": data.get("infocode")})


def search_poi_around(
    *,
    api_key: str | None,
    keyword: str | None,
    types: str | None,
    location: str,
    radius_m: int,
    limit: int,
    timeout_s: float,
) -> dict:
    if not api_key:
        raise AdapterError("MISSING_API_KEY", "AMAP_API_KEY is not set")

    params: dict[str, str | int] = {
        "key": api_key,
        "location": location,
        "radius": radius_m,
        "offset": limit,
        "extensions": "base",
    }
    if keyword:
        params["keywords"] = keyword
    if types:
        params["types"] = types

    url = f"{AMAP_BASE_URL}/place/around"
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url, params=params)
    data = resp.json()
    _raise_for_status(data)
    return data


def geocode_address(
    *,
    api_key: str | None,
    address: str,
    city: str | None,
    timeout_s: float,
) -> dict:
    if not api_key:
        raise AdapterError("MISSING_API_KEY", "AMAP_API_KEY is not set")

    params: dict[str, str] = {
        "key": api_key,
        "address": address,
        "output": "JSON",
    }
    if city:
        params["city"] = city

    url = f"{AMAP_BASE_URL}/geocode/geo"
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url, params=params)
    data = resp.json()
    _raise_for_status(data)
    if not data.get("geocodes"):
        raise AdapterError("NOT_FOUND", "No geocode results", {"address": address})
    return data
