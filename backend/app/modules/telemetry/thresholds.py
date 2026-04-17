THRESHOLDS: dict[str, float] = {
    "engine_temp": 110.0,
    "fuel_level": 10.0,
    "speed": 80.0,
    "payload_weight": 60.0,
}

THRESHOLD_DIRECTION: dict[str, str] = {
    "engine_temp": "above",
    "fuel_level": "below",
    "speed": "above",
    "payload_weight": "above",
}

def exceeds_threshold(sensor_type: str, normalized_value: float) -> bool:
    threshold = THRESHOLDS.get(sensor_type)
    if threshold is None:
        return False
    direction = THRESHOLD_DIRECTION.get(sensor_type, "above")
    if direction == "above":
        return normalized_value > threshold
    return normalized_value < threshold

# Telemetry-derived machine state logic
def derive_machine_state(readings: dict[str, float]) -> str | None:
    engine_temp = readings.get("engine_temp")
    speed = readings.get("speed")
    fuel_level = readings.get("fuel_level")

    if engine_temp is not None and engine_temp > THRESHOLDS["engine_temp"]:
        return "breakdown"
    if fuel_level is not None and fuel_level < 5.0:
        return "maintenance"
    if speed is not None and speed > 0:
        return "operating"
    if speed is not None and speed == 0:
        return "idle"
    return None
