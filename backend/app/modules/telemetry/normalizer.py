from typing import Callable

NORMALIZERS: dict[str, dict[str, Callable[[float], float]]] = {
    "engine_temp": {
        "celsius": lambda v: v,
        "fahrenheit": lambda v: (v - 32) * (5 / 9),
    },
    "fuel_level": {
        "percent": lambda v: v,
    },
    "speed": {
        "kmh": lambda v: v,
        "mph": lambda v: v * 1.60934,
    },
    "payload_weight": {
        "tonnes": lambda v: v,
        "kg": lambda v: v / 1000,
    },
}

CANONICAL_UNITS: dict[str, str] = {
    "engine_temp": "celsius",
    "fuel_level": "percent",
    "speed": "kmh",
    "payload_weight": "tonnes",
}

def normalize(sensor_type: str, value: float, unit: str) -> float:
    sensor_normalizers = NORMALIZERS.get(sensor_type)
    if sensor_normalizers is None:
        raise ValueError(f"Unknown sensor_type: {sensor_type}")
    normalizer_fn = sensor_normalizers.get(unit)
    if normalizer_fn is None:
        raise ValueError(f"Unknown unit '{unit}' for sensor_type '{sensor_type}'")
    return normalizer_fn(value)
