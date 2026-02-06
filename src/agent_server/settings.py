"""Agent server configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE, override=False)


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="A2A_MCP_", env_file=str(ENV_FILE), extra="ignore")

    host: str = "0.0.0.0"
    port: int = 7002

    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "A2A_MCP_OPENAI_API_KEY"),
    )
    openai_model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tool_calls: int = 3
    openai_timeout_s: float = 20.0

    mcp_base_url: str = "http://localhost:7001"
    request_timeout_s: float = 10.0

    mock_llm: bool = False
    trace_enabled: bool = True
    trace_dir: str = "traces"


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    return AgentSettings()
