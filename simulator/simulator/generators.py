import random

SENSOR_TYPES = ["engine_temp", "fuel_level", "speed", "payload_weight"]

def generate_engine_temp() -> dict:
    # Occasionally spike above 110°C threshold to trigger anomalies
    value = random.uniform(60, 130)
    return {"value": round(value, 2), "unit": "celsius"}

def generate_fuel_level() -> dict:
    # Occasionally dip below 10% threshold
    value = random.uniform(0, 100)
    return {"value": round(value, 2), "unit": "percent"}

def generate_speed() -> dict:
    # Occasionally exceed 80 kmh threshold
    value = random.uniform(0, 90)
    return {"value": round(value, 2), "unit": "kmh"}

def generate_payload_weight() -> dict:
    # Occasionally exceed 60t threshold
    value = random.uniform(0, 70)
    return {"value": round(value, 2), "unit": "tonnes"}

GENERATORS = {
    "engine_temp": generate_engine_temp,
    "fuel_level": generate_fuel_level,
    "speed": generate_speed,
    "payload_weight": generate_payload_weight,
}

def update_position(pos_x: float, pos_y: float) -> tuple[float, float]:
    """Random walk within a bounded quarry grid (0–800, 0–500)."""
    new_x = max(0.0, min(800.0, pos_x + random.uniform(-10, 10)))
    new_y = max(0.0, min(500.0, pos_y + random.uniform(-10, 10)))
    return round(new_x, 2), round(new_y, 2)
