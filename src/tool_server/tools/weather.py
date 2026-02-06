"""Weather tool."""

from __future__ import annotations

from ..adapters.amap import geocode_address
from ..adapters.openweather import fetch_current_weather
from ..schemas import WeatherInput, WeatherOutput
from ..settings import ToolServerSettings


def get_weather(payload: WeatherInput, settings: ToolServerSettings, _trace_id: str) -> WeatherOutput:
    # Delegate upstream call to adapter; keep tool thin.
    city = payload.city
    lat = payload.lat
    lon = payload.lon

    # If city is non-ASCII (e.g. Chinese), try mapping or AMap geocode.
    if city and not city.isascii():
        mapped = _normalize_city(city)
        if mapped:
            city = mapped
        elif settings.amap_api_key:
            geocode = geocode_address(
                api_key=settings.amap_api_key,
                address=city,
                city=city,
                timeout_s=settings.request_timeout_s,
            )
            location = geocode.get("geocodes", [{}])[0].get("location", "")
            if location and "," in location:
                lon_str, lat_str = location.split(",")
                lon = float(lon_str)
                lat = float(lat_str)

    data = fetch_current_weather(
        api_key=settings.openweather_api_key,
        city=city,
        lat=lat,
        lon=lon,
        units=payload.units,
        lang=payload.lang or settings.default_lang,
        timeout_s=settings.request_timeout_s,
    )

    weather_desc = None
    if data.get("weather"):
        weather_desc = data["weather"][0].get("description")

    main = data.get("main", {})
    wind = data.get("wind", {})

    return WeatherOutput(
        source="openweather",
        city=data.get("name") or city,
        lat=data.get("coord", {}).get("lat"),
        lon=data.get("coord", {}).get("lon"),
        description=weather_desc,
        temperature_c=main.get("temp"),
        feels_like_c=main.get("feels_like"),
        humidity=main.get("humidity"),
        wind_speed=wind.get("speed"),
        observation_time=str(data.get("dt")) if data.get("dt") else None,
    )


def _normalize_city(city: str) -> str | None:
    """Best-effort mapping for common Chinese city names."""
    mapping = {
        "北京": "Beijing",
        "上海": "Shanghai",
        "广州": "Guangzhou",
        "深圳": "Shenzhen",
        "杭州": "Hangzhou",
        "成都": "Chengdu",
        "西安": "Xi'an",
        "重庆": "Chongqing",
        "南京": "Nanjing",
        "武汉": "Wuhan",
    }
    return mapping.get(city)
