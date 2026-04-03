from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Wallet API"
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@db:5432/wallet_db"
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
