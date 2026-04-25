"""
Sensor thresholds and telemetry-derived machine state logic.
All threshold values are defined here as named constants — never inline.
"""

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

# Separate critical threshold for fuel — triggers maintenance state, not just anomaly alert
FUEL_CRITICAL_THRESHOLD: float = 5.0


def exceeds_threshold(sensor_type: str, normalized_value: float) -> bool:
    threshold = THRESHOLDS.get(sensor_type)
    if threshold is None:
        return False
    direction = THRESHOLD_DIRECTION.get(sensor_type, "above")
    if direction == "above":
        return normalized_value > threshold
    return normalized_value < threshold


def derive_machine_state(readings: dict[str, float]) -> str | None:
    """
    Derive a machine state from a set of sensor readings.
    Priority: breakdown > maintenance > operating > idle.
    Returns None if no state can be determined.
    """
    engine_temp = readings.get("engine_temp")
    speed = readings.get("speed")
    fuel_level = readings.get("fuel_level")

    if engine_temp is not None and engine_temp > THRESHOLDS["engine_temp"]:
        return "breakdown"
    if fuel_level is not None and fuel_level < FUEL_CRITICAL_THRESHOLD:
        return "maintenance"
    if speed is not None and speed > 0:
        return "operating"
    if speed is not None and speed == 0:
        return "idle"
    return None
