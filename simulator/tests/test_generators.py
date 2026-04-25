"""
Tests for simulator/generators.py — pure functions, no backend needed.
"""
import math
import pytest
from unittest.mock import MagicMock
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from simulator.generators import (
    compute_antenna_estimate,
    find_nearest_antenna,
    generate_engine_temp,
    generate_fuel_level,
    generate_payload_weight,
    generate_speed,
    update_position,
    GENERATORS,
    SENSOR_TYPES,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_settings(
    min_lat=-26.2100, max_lat=-26.1980,
    min_lng=28.0400, max_lng=28.0550,
):
    s = MagicMock()
    s.QUARRY_MIN_LAT = min_lat
    s.QUARRY_MAX_LAT = max_lat
    s.QUARRY_MIN_LNG = min_lng
    s.QUARRY_MAX_LNG = max_lng
    return s


MOCK_SETTINGS = make_settings()

SAMPLE_ANTENNAS = [
    {"name": "Antenna A", "lat": -26.2035, "lng": 28.0460},
    {"name": "Antenna B", "lat": -26.2050, "lng": 28.0490},
    {"name": "Antenna C", "lat": -26.2030, "lng": 28.0500},
]


# ---------------------------------------------------------------------------
# Sensor generator tests
# ---------------------------------------------------------------------------

def test_generate_engine_temp_range():
    for _ in range(200):
        r = generate_engine_temp()
        assert 60.0 <= r["value"] <= 130.0
        assert r["unit"] == "celsius"


def test_generate_fuel_level_range():
    for _ in range(200):
        r = generate_fuel_level()
        assert 0.0 <= r["value"] <= 100.0
        assert r["unit"] == "percent"


def test_generate_speed_range():
    for _ in range(200):
        r = generate_speed()
        assert 0.0 <= r["value"] <= 90.0
        assert r["unit"] == "kmh"


def test_generate_payload_weight_range():
    for _ in range(200):
        r = generate_payload_weight()
        assert 0.0 <= r["value"] <= 70.0
        assert r["unit"] == "tonnes"


def test_generators_dict_covers_all_sensor_types():
    assert set(GENERATORS.keys()) == set(SENSOR_TYPES)


def test_all_generators_return_finite_values():
    for name, gen in GENERATORS.items():
        for _ in range(50):
            r = gen()
            assert math.isfinite(r["value"]), f"{name} returned non-finite value"


# ---------------------------------------------------------------------------
# update_position — stays within bounds
# ---------------------------------------------------------------------------

@given(
    lat=st.floats(min_value=-26.2100, max_value=-26.1980),
    lng=st.floats(min_value=28.0400, max_value=28.0550),
)
@h_settings(max_examples=200)
def test_update_position_stays_in_bounds(lat: float, lng: float):
    """Random walk always stays within quarry bounding box."""
    new_lat, new_lng = update_position(lat, lng, MOCK_SETTINGS)
    assert MOCK_SETTINGS.QUARRY_MIN_LAT <= new_lat <= MOCK_SETTINGS.QUARRY_MAX_LAT
    assert MOCK_SETTINGS.QUARRY_MIN_LNG <= new_lng <= MOCK_SETTINGS.QUARRY_MAX_LNG


def test_update_position_returns_finite():
    lat, lng = update_position(-26.2041, 28.0473, MOCK_SETTINGS)
    assert math.isfinite(lat)
    assert math.isfinite(lng)


def test_update_position_clamps_at_min_bounds():
    """Position at exact min bound stays at or above min."""
    lat, lng = update_position(
        MOCK_SETTINGS.QUARRY_MIN_LAT,
        MOCK_SETTINGS.QUARRY_MIN_LNG,
        MOCK_SETTINGS,
    )
    assert lat >= MOCK_SETTINGS.QUARRY_MIN_LAT
    assert lng >= MOCK_SETTINGS.QUARRY_MIN_LNG


def test_update_position_clamps_at_max_bounds():
    """Position at exact max bound stays at or below max."""
    lat, lng = update_position(
        MOCK_SETTINGS.QUARRY_MAX_LAT,
        MOCK_SETTINGS.QUARRY_MAX_LNG,
        MOCK_SETTINGS,
    )
    assert lat <= MOCK_SETTINGS.QUARRY_MAX_LAT
    assert lng <= MOCK_SETTINGS.QUARRY_MAX_LNG


# ---------------------------------------------------------------------------
# compute_antenna_estimate — Gaussian noise bounds
# ---------------------------------------------------------------------------

@given(
    lat=st.floats(min_value=-90, max_value=90),
    lng=st.floats(min_value=-180, max_value=180),
    sigma=st.floats(min_value=1e-8, max_value=0.001),
)
@h_settings(max_examples=200)
def test_compute_antenna_estimate_within_5_sigma(lat: float, lng: float, sigma: float):
    """Estimate stays within 5σ of true position (probabilistic bound)."""
    est_lat, est_lng = compute_antenna_estimate(lat, lng, sigma)
    assert abs(est_lat - lat) <= 5 * sigma, f"lat deviation {abs(est_lat - lat)} > 5σ={5*sigma}"
    assert abs(est_lng - lng) <= 5 * sigma, f"lng deviation {abs(est_lng - lng)} > 5σ={5*sigma}"


def test_compute_antenna_estimate_returns_finite():
    est_lat, est_lng = compute_antenna_estimate(-26.2041, 28.0473, 0.000018)
    assert math.isfinite(est_lat)
    assert math.isfinite(est_lng)


def test_compute_antenna_estimate_zero_sigma_returns_original():
    """Zero noise → estimate equals original position."""
    lat, lng = -26.2041, 28.0473
    est_lat, est_lng = compute_antenna_estimate(lat, lng, 0.0)
    assert est_lat == pytest.approx(lat, abs=1e-6)
    assert est_lng == pytest.approx(lng, abs=1e-6)


# ---------------------------------------------------------------------------
# find_nearest_antenna
# ---------------------------------------------------------------------------

def test_find_nearest_antenna_returns_closest():
    """Returns the antenna with smallest Euclidean distance."""
    antennas = [
        {"name": "Far", "lat": -26.2000, "lng": 28.0400},
        {"name": "Near", "lat": -26.2041, "lng": 28.0473},
        {"name": "Medium", "lat": -26.2020, "lng": 28.0450},
    ]
    result = find_nearest_antenna(-26.2041, 28.0473, antennas)
    assert result["name"] == "Near"


def test_find_nearest_antenna_single_antenna():
    """Single antenna always returned."""
    antennas = [{"name": "Only", "lat": 0.0, "lng": 0.0}]
    result = find_nearest_antenna(10.0, 10.0, antennas)
    assert result["name"] == "Only"


def test_find_nearest_antenna_with_sample_antennas():
    """Machine near Antenna B → Antenna B returned."""
    # Position very close to Antenna B
    result = find_nearest_antenna(-26.2051, 28.0491, SAMPLE_ANTENNAS)
    assert result["name"] == "Antenna B"


@given(
    lat=st.floats(min_value=-90, max_value=90),
    lng=st.floats(min_value=-180, max_value=180),
)
@h_settings(max_examples=100)
def test_find_nearest_antenna_always_returns_valid_antenna(lat: float, lng: float):
    """Always returns one of the configured antennas."""
    result = find_nearest_antenna(lat, lng, SAMPLE_ANTENNAS)
    assert result in SAMPLE_ANTENNAS
