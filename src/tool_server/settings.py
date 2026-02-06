"""Tool server configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE, override=False)


class ToolServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="A2A_MCP_", env_file=str(ENV_FILE), extra="ignore")

    host: str = "0.0.0.0"
    port: int = 7001

    openweather_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENWEATHER_API_KEY", "A2A_MCP_OPENWEATHER_API_KEY"),
    )
    amap_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AMAP_API_KEY", "A2A_MCP_AMAP_API_KEY"),
    )

    request_timeout_s: float = 8.0
    default_timezone: str = "Asia/Shanghai"
    default_lang: str = "zh_cn"


@lru_cache(maxsize=1)
def get_settings() -> ToolServerSettings:
    return ToolServerSettings()
