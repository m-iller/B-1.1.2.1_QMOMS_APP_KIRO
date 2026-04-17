"""
Property-based tests for the telemetry module.
Feature: quarry-mining-monitor
"""
import math
import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.modules.telemetry.normalizer import normalize, CANONICAL_UNITS, NORMALIZERS
from app.modules.telemetry.thresholds import exceeds_threshold, THRESHOLDS, THRESHOLD_DIRECTION

# ---------------------------------------------------------------------------
# Property 13: Telemetry Validation — Invalid Payloads Not Persisted
# IngestTelemetryRequest must reject non-finite values and unknown sensor types.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 13: Telemetry Validation — Invalid Payloads Not Persisted
# Validates: Requirements 4.2, 4.3
@given(
    bad_value=st.one_of(
        st.just(float("nan")),
        st.just(float("inf")),
        st.just(float("-inf")),
    )
)
@h_settings(max_examples=100)
def test_non_finite_value_rejected(bad_value: float):
    from app.modules.telemetry.schemas import IngestTelemetryRequest
    with pytest.raises(ValidationError):
        IngestTelemetryRequest(
            machine_id="some-id",
            sensor_type="engine_temp",
            value=bad_value,
            unit="celsius",
            timestamp="2024-01-01T00:00:00Z",
        )


@given(
    unknown_sensor=st.text(min_size=1, max_size=30).filter(
        lambda s: s not in {"engine_temp", "fuel_level", "speed", "payload_weight"}
    )
)
@h_settings(max_examples=100)
def test_unknown_sensor_type_rejected(unknown_sensor: str):
    from app.modules.telemetry.schemas import IngestTelemetryRequest
    with pytest.raises(ValidationError):
        IngestTelemetryRequest(
            machine_id="some-id",
            sensor_type=unknown_sensor,
            value=50.0,
            unit="celsius",
            timestamp="2024-01-01T00:00:00Z",
        )


# ---------------------------------------------------------------------------
# Property 14: Telemetry Normalization Correctness
# For each sensor_type and accepted unit, normalize() must return the
# mathematically correct conversion.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 14: Telemetry Normalization Correctness
# Validates: Requirements 4.4, 4.6

@given(value=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_celsius_normalization_identity(value: float):
    result = normalize("engine_temp", value, "celsius")
    assert abs(result - value) < 1e-9


@given(value=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_fahrenheit_to_celsius_normalization(value: float):
    result = normalize("engine_temp", value, "fahrenheit")
    expected = (value - 32) * (5 / 9)
    assert abs(result - expected) < 1e-9


@given(value=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_fuel_level_percent_identity(value: float):
    result = normalize("fuel_level", value, "percent")
    assert abs(result - value) < 1e-9


@given(value=st.floats(min_value=0, max_value=200, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_speed_kmh_identity(value: float):
    result = normalize("speed", value, "kmh")
    assert abs(result - value) < 1e-9


@given(value=st.floats(min_value=0, max_value=200, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_speed_mph_to_kmh(value: float):
    result = normalize("speed", value, "mph")
    expected = value * 1.60934
    assert abs(result - expected) < 1e-6


@given(value=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_payload_tonnes_identity(value: float):
    result = normalize("payload_weight", value, "tonnes")
    assert abs(result - value) < 1e-9


@given(value=st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_payload_kg_to_tonnes(value: float):
    result = normalize("payload_weight", value, "kg")
    expected = value / 1000
    assert abs(result - expected) < 1e-9


def test_normalize_unknown_sensor_raises():
    with pytest.raises(ValueError, match="Unknown sensor_type"):
        normalize("unknown_sensor", 50.0, "celsius")


def test_normalize_unknown_unit_raises():
    with pytest.raises(ValueError, match="Unknown unit"):
        normalize("engine_temp", 50.0, "kelvin")


# ---------------------------------------------------------------------------
# Property 15: Anomaly Detection Side-Effects
# exceeds_threshold() must correctly identify values above/below thresholds.
# ---------------------------------------------------------------------------
# Feature: quarry-mining-monitor, Property 15: Anomaly Detection Side-Effects
# Validates: Requirements 4.7

@given(value=st.floats(min_value=110.01, max_value=500, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_engine_temp_above_threshold_is_anomaly(value: float):
    assert exceeds_threshold("engine_temp", value) is True


@given(value=st.floats(min_value=-100, max_value=109.99, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_engine_temp_below_threshold_is_not_anomaly(value: float):
    assert exceeds_threshold("engine_temp", value) is False


@given(value=st.floats(min_value=0, max_value=9.99, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_fuel_level_below_threshold_is_anomaly(value: float):
    # fuel_level uses "below" direction
    assert exceeds_threshold("fuel_level", value) is True


@given(value=st.floats(min_value=10.01, max_value=100, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_fuel_level_above_threshold_is_not_anomaly(value: float):
    assert exceeds_threshold("fuel_level", value) is False


@given(value=st.floats(min_value=80.01, max_value=200, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_speed_above_threshold_is_anomaly(value: float):
    assert exceeds_threshold("speed", value) is True


@given(value=st.floats(min_value=60.01, max_value=100, allow_nan=False, allow_infinity=False))
@h_settings(max_examples=100)
def test_payload_above_threshold_is_anomaly(value: float):
    assert exceeds_threshold("payload_weight", value) is True
