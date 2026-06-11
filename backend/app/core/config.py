from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "HummingID"
    app_env: str = "dev"
    api_v1_prefix: str = "/api/v1"

    max_upload_bytes: int = 5 * 1024 * 1024
    max_audio_seconds: int = 30
    allowed_mime: list[str] = Field(
        default_factory=lambda: [
            "audio/wav",
            "audio/mpeg",
            "audio/mp4",
            "audio/ogg",
            "audio/webm",
        ]
    )

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
