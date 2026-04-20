from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_URL: str = "http://localhost:8000"
    API_TOKEN: str = "sim_token_changeme"
    INTERVAL_MS: int = 5000
    # Comma-separated machine IDs to simulate; if empty, fetched from API
    MACHINE_IDS: str = ""

    # Quarry bounding box for lat/lng random walk (Johannesburg area defaults)
    QUARRY_MIN_LAT: float = -26.2100
    QUARRY_MAX_LAT: float = -26.1980
    QUARRY_MIN_LNG: float = 28.0400
    QUARRY_MAX_LNG: float = 28.0550

    # Antenna definitions as JSON string: [{"name":"A","lat":...,"lng":...}, ...]
    # Number of antennas is configurable — add/remove entries here
    ANTENNAS_JSON: str = (
        '[{"name":"Antenna A","lat":-26.2035,"lng":28.0460},'
        '{"name":"Antenna B","lat":-26.2050,"lng":28.0490},'
        '{"name":"Antenna C","lat":-26.2030,"lng":28.0500}]'
    )

    # Gaussian noise std dev in degrees (≈ 2m at equator ≈ 0.000018 degrees)
    POSITION_NOISE_STD: float = 0.000018


settings = Settings()
