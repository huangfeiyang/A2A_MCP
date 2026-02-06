"""POI tool."""

from __future__ import annotations

from ..adapters.amap import geocode_address, search_poi_around
from ..schemas import PoiInput, PoiItem, PoiOutput
from ..settings import ToolServerSettings


def _parse_location(poi: dict) -> tuple[float, float]:
    # AMap returns "lon,lat" string.
    location = poi.get("location", "")
    if not location:
        return 0.0, 0.0
    lon_str, lat_str = location.split(",")
    return float(lat_str), float(lon_str)


def search_poi(payload: PoiInput, settings: ToolServerSettings, _trace_id: str) -> PoiOutput:
    # AMap "around" API needs a coordinate.
    if payload.lat is not None and payload.lon is not None:
        location = f"{payload.lon},{payload.lat}"
    elif payload.city:
        geocode = geocode_address(
            api_key=settings.amap_api_key,
            address=payload.city,
            city=payload.city,
            timeout_s=settings.request_timeout_s,
        )
        location = geocode.get("geocodes", [{}])[0].get("location", "")
        if not location:
            raise ValueError(f"Unable to geocode city: {payload.city}")
    else:
        raise ValueError("Missing location or city for POI search")

    data = search_poi_around(
        api_key=settings.amap_api_key,
        keyword=payload.keyword,
        types=payload.types,
        location=location,
        radius_m=payload.radius_m,
        limit=payload.limit,
        timeout_s=settings.request_timeout_s,
    )

    items: list[PoiItem] = []
    for poi in data.get("pois", []):
        lat, lon = _parse_location(poi)
        items.append(
            PoiItem(
                name=poi.get("name", ""),
                address=poi.get("address"),
                lat=lat,
                lon=lon,
                distance_m=int(poi.get("distance", 0)) if poi.get("distance") else None,
            )
        )

    return PoiOutput(city=payload.city, keyword=payload.keyword, items=items)
