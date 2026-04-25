from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    API_URL: str = "http://localhost:8000"
    API_TOKEN: str = "sim_token_changeme"
    INTERVAL_MS: int = 5000

    # Comma-separated machine IDs to simulate; if empty, fetched from API
    MACHINE_IDS: str = ""

    # Max deviation from map center in degrees
    # Bounding box is computed at runtime: center ± POSITION_RADIUS
    POSITION_RADIUS: float = 0.1

    # Antenna definitions as JSON string: [{"name":"A","lat":...,"lng":...}, ...]
    # If empty, antennas are fetched from GET /map-config at startup
    ANTENNAS_JSON: str = ""

    # Gaussian noise std dev in degrees (≈ 2m at equator ≈ 0.000018 degrees)
    POSITION_NOISE_STD: float = 0.0002

    # --- Task simulation ---
    # Probability per machine per tick of creating a new task (0.0–1.0)
    TASK_CREATE_PROB: float = 0.05
    # Probability per active task per tick of advancing its state
    TASK_ADVANCE_PROB: float = 0.1
    # Max concurrent tasks per machine
    TASK_MAX_PER_MACHINE: int = 3

    # --- Machine state simulation ---
    # Probability per machine per tick of changing state (0.0–1.0)
    STATE_CHANGE_PROB: float = 0.03


settings = Settings()
