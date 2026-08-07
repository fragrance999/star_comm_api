from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "star_comm_api"
    app_env: str = "local"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://starcomm:starcomm@localhost:5432/starcomm"
    sql_echo: bool = False
    sql_echo_parameters: bool = False
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = Field(default="change-me-in-local-env")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 30

    register_mode: str = "INVITE_OPTIONAL"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
