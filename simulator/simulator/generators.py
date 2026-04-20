import math
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


def update_position(lat: float, lng: float, settings) -> tuple[float, float]:
    """Random walk within the configured quarry bounding box (lat/lng degrees)."""
    step = 0.0002  # ~22m per step at equator
    new_lat = lat + random.uniform(-step, step)
    new_lng = lng + random.uniform(-step, step)
    # Clamp to quarry bounds
    new_lat = max(settings.QUARRY_MIN_LAT, min(settings.QUARRY_MAX_LAT, new_lat))
    new_lng = max(settings.QUARRY_MIN_LNG, min(settings.QUARRY_MAX_LNG, new_lng))
    return round(new_lat, 7), round(new_lng, 7)


def compute_antenna_estimate(lat: float, lng: float, sigma: float) -> tuple[float, float]:
    """Add Gaussian noise to a position to simulate antenna-based measurement error."""
    est_lat = lat + random.gauss(0, sigma)
    est_lng = lng + random.gauss(0, sigma)
    return round(est_lat, 7), round(est_lng, 7)


def find_nearest_antenna(lat: float, lng: float, antennas: list[dict]) -> dict:
    """Return the antenna closest to (lat, lng) using Euclidean distance."""
    def dist(a: dict) -> float:
        return math.sqrt((a["lat"] - lat) ** 2 + (a["lng"] - lng) ** 2)
    return min(antennas, key=dist)
