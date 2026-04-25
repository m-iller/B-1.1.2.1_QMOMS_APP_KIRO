"""
Telemetry data generators for the quarry simulator.
All sensor ranges are defined as named constants — never inline magic numbers.
"""
import math
import random

SENSOR_TYPES = ["engine_temp", "fuel_level", "speed", "payload_weight"]

# Sensor value ranges (min, max) for random generation
# Ranges are intentionally wide enough to occasionally exceed anomaly thresholds
ENGINE_TEMP_RANGE = (60.0, 130.0)   # threshold: 110°C
FUEL_LEVEL_RANGE = (0.0, 100.0)     # threshold: <10%
SPEED_RANGE = (0.0, 90.0)           # threshold: 80 km/h
PAYLOAD_WEIGHT_RANGE = (0.0, 70.0)  # threshold: 60t

# Position random walk step size in degrees (~22m at equator)
POSITION_STEP_DEGREES = 0.0002


def generate_engine_temp() -> dict:
    value = random.uniform(*ENGINE_TEMP_RANGE)
    return {"value": round(value, 2), "unit": "celsius"}


def generate_fuel_level() -> dict:
    value = random.uniform(*FUEL_LEVEL_RANGE)
    return {"value": round(value, 2), "unit": "percent"}


def generate_speed() -> dict:
    value = random.uniform(*SPEED_RANGE)
    return {"value": round(value, 2), "unit": "kmh"}


def generate_payload_weight() -> dict:
    value = random.uniform(*PAYLOAD_WEIGHT_RANGE)
    return {"value": round(value, 2), "unit": "tonnes"}


GENERATORS = {
    "engine_temp": generate_engine_temp,
    "fuel_level": generate_fuel_level,
    "speed": generate_speed,
    "payload_weight": generate_payload_weight,
}


def compute_antenna_estimate(lat: float, lng: float, noise_std_degrees: float) -> tuple[float, float]:
    """Add Gaussian noise to a position to simulate antenna-based measurement error."""
    estimated_lat = lat + random.gauss(0, noise_std_degrees)
    estimated_lng = lng + random.gauss(0, noise_std_degrees)
    return round(estimated_lat, 7), round(estimated_lng, 7)


def find_nearest_antenna(lat: float, lng: float, antennas: list[dict]) -> dict:
    """Return the antenna closest to (lat, lng) using Euclidean distance."""
    def euclidean_distance(antenna: dict) -> float:
        return math.sqrt((antenna["lat"] - lat) ** 2 + (antenna["lng"] - lng) ** 2)
    return min(antennas, key=euclidean_distance)
