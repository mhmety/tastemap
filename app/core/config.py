from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TasteMap"
    debug: bool = False
    database_url: str = "postgresql://tastemap:tastemap@db:5432/tastemap"


settings = Settings()
