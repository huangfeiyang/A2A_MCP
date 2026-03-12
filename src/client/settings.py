"""Client configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class ClientSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    agent_base_url: str = Field(
        default="http://localhost:7002",
        validation_alias=AliasChoices("A2A_MCP_AGENT_BASE_URL", "AGENT_URL"),
    )
    timeout_s: float = Field(
        default=60.0,
        validation_alias=AliasChoices("A2A_MCP_CLIENT_TIMEOUT_S"),
    )


@lru_cache(maxsize=1)
def get_settings() -> ClientSettings:
    return ClientSettings()
