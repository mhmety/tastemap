from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "TasteMap"
    debug: bool = False
    database_url: str = "postgresql://tastemap:tastemap@db:5432/tastemap"
    
    # JWT Settings
    secret_key: str 
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


settings = Settings()
