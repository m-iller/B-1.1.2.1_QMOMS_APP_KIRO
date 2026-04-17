from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_URL: str = "http://localhost:8000"
    API_TOKEN: str = "sim_token_changeme"
    INTERVAL_MS: int = 5000
    # Comma-separated machine IDs to simulate; if empty, fetched from API
    MACHINE_IDS: str = ""

settings = Settings()
