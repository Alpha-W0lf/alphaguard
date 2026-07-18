"""Runtime settings from environment (.env / .env.example)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

RepoRoot = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    alphaguard_mode: Literal["replay", "live"] = "replay"
    alphaguard_rag_mode: Literal["fixture", "qdrant"] = "fixture"
    ollama_model: str = "gemma4:e2b"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_fallback_model: str = "qwen3.5:4b"

    kafka_bootstrap_servers: str = "localhost:9092"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "alphaguard_news"

    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "alphaguard"
    phoenix_enabled: bool = False
    # Optional overrides (attempt gate remains phoenix_enabled alone — Guide 08 lock A)
    phoenix_collector_endpoint: str | None = None
    phoenix_project_name: str = "alphaguard"

    fixtures_dir: Path = Field(default=RepoRoot / "data" / "fixtures")
    artifacts_dir: Path = Field(default=RepoRoot / "artifacts")
    model_bundle_dir: Path = Field(
        default=RepoRoot / "data" / "fixtures" / "model_bundle_fixture"
    )
    top_k: int = 5

    @property
    def resource_mode(self) -> Literal[
        "replay_fixture", "replay_qdrant", "kafka_integration"
    ]:
        if self.alphaguard_mode == "live" and self.alphaguard_rag_mode == "qdrant":
            return "kafka_integration"
        if self.alphaguard_rag_mode == "qdrant":
            return "replay_qdrant"
        return "replay_fixture"


def get_settings() -> Settings:
    return Settings()
