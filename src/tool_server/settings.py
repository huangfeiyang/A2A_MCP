"""Tool server configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class ToolServerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("A2A_MCP_TOOL_HOST"))
    port: int = Field(default=7001, validation_alias=AliasChoices("A2A_MCP_TOOL_PORT"))
    reload: bool = Field(default=False, validation_alias=AliasChoices("A2A_MCP_RELOAD"))
    service_title: str = Field(
        default="A2A MCP Tool Server",
        validation_alias=AliasChoices("A2A_MCP_TOOL_TITLE"),
    )
    service_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("A2A_MCP_TOOL_VERSION"),
    )

    openweather_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENWEATHER_API_KEY", "A2A_MCP_OPENWEATHER_API_KEY"),
    )
    amap_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AMAP_API_KEY", "A2A_MCP_AMAP_API_KEY"),
    )

    request_timeout_s: float = Field(
        default=8.0,
        validation_alias=AliasChoices("A2A_MCP_TOOL_REQUEST_TIMEOUT_S"),
    )
    default_timezone: str = Field(
        default="Asia/Shanghai",
        validation_alias=AliasChoices("A2A_MCP_TOOL_DEFAULT_TIMEZONE"),
    )
    default_lang: str = Field(
        default="zh_cn",
        validation_alias=AliasChoices("A2A_MCP_TOOL_DEFAULT_LANG"),
    )


@lru_cache(maxsize=1)
def get_settings() -> ToolServerSettings:
    return ToolServerSettings()
