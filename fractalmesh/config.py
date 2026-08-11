from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    database_url: str = Field("sqlite:///fractalmesh.db", alias="DATABASE_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_json: bool = Field(False, alias="LOG_JSON")
    embedding_provider: str = Field("hash", alias="EMBEDDING_PROVIDER")
    openai_api_key: SecretStr | None = Field(None, alias="OPENAI_API_KEY")
    vector_backend: str = Field("sqlite", alias="VECTOR_BACKEND")
    chroma_host: str = Field("localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(8000, alias="CHROMA_PORT")
    rss_sources_file: str = Field("", alias="RSS_SOURCES_FILE")
    mcp_servers_config: str = Field("", alias="MCP_SERVERS_CONFIG")
    rl_exploration_rate: float = Field(0.1, alias="RL_EXPLORATION_RATE")
    memory_consolidation_threshold: int = Field(
        1000,
        alias="MEMORY_CONSOLIDATION_THRESHOLD",
    )
    rate_limit_requests_per_minute: int = Field(
        60,
        alias="RATE_LIMIT_REQUESTS_PER_MINUTE",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )
