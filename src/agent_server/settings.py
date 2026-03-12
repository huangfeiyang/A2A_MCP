"""Agent server configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), extra="ignore")

    host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("A2A_MCP_AGENT_HOST"))
    port: int = Field(default=7002, validation_alias=AliasChoices("A2A_MCP_AGENT_PORT"))
    reload: bool = Field(default=False, validation_alias=AliasChoices("A2A_MCP_RELOAD"))
    service_title: str = Field(
        default="A2A Agent Server",
        validation_alias=AliasChoices("A2A_MCP_AGENT_TITLE"),
    )
    agent_name: str = Field(
        default="autocity-agent",
        validation_alias=AliasChoices("A2A_MCP_AGENT_NAME"),
    )
    agent_version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("A2A_MCP_AGENT_VERSION"),
    )
    agent_description: str = Field(
        default="Single agent demo with MCP tool server.",
        validation_alias=AliasChoices("A2A_MCP_AGENT_DESCRIPTION"),
    )

    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "A2A_MCP_OPENAI_API_KEY"),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_BASE_URL", "A2A_MCP_OPENAI_BASE_URL"),
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("A2A_MCP_OPENAI_MODEL"),
    )
    temperature: float = Field(
        default=0.2,
        validation_alias=AliasChoices("A2A_MCP_OPENAI_TEMPERATURE", "A2A_MCP_TEMPERATURE"),
    )
    max_tool_calls: int = Field(
        default=3,
        validation_alias=AliasChoices("A2A_MCP_MAX_TOOL_CALLS"),
    )
    tool_arg_retry_limit: int = Field(
        default=1,
        validation_alias=AliasChoices("A2A_MCP_TOOL_ARG_RETRY_LIMIT"),
    )
    openai_timeout_s: float = Field(
        default=20.0,
        validation_alias=AliasChoices("A2A_MCP_OPENAI_TIMEOUT_S"),
    )

    mcp_base_url: str = Field(
        default="http://localhost:7001",
        validation_alias=AliasChoices("A2A_MCP_MCP_BASE_URL"),
    )
    request_timeout_s: float = Field(
        default=10.0,
        validation_alias=AliasChoices(
            "A2A_MCP_AGENT_REQUEST_TIMEOUT_S",
            "A2A_MCP_REQUEST_TIMEOUT_S",
        ),
    )

    mock_llm: bool = Field(default=False, validation_alias=AliasChoices("A2A_MCP_MOCK_LLM"))
    trace_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("A2A_MCP_TRACE_ENABLED"),
    )
    trace_dir: str = Field(default="traces", validation_alias=AliasChoices("A2A_MCP_TRACE_DIR"))


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    return AgentSettings()
