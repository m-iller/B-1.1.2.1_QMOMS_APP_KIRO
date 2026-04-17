from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/quarry"
    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRES_IN: int = 3600  # seconds
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()
