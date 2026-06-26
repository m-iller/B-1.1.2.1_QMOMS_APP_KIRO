"""
Connectivity diagnostic tests for the simulator → backend connection.

Run with:
    cd simulator
    pytest tests/test_connectivity.py -v

These tests hit the REAL backend at API_URL from simulator/.env.
They are diagnostic — they tell you exactly what is wrong.

Note: Telemetry ingestion is now unauthenticated for simulator use.
Other endpoints still require authentication.
"""
import asyncio
import pytest
import httpx

from simulator.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


async def _get(path: str, token: str | None = None) -> httpx.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # trust_env=False bypasses system proxy settings (corporate proxy/VPN)
    async with httpx.AsyncClient(
        base_url=settings.API_URL, timeout=5.0, trust_env=False
    ) as client:
        return await client.get(path, headers=headers)


async def _post(path: str, json: dict, token: str | None = None) -> httpx.Response:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # trust_env=False bypasses system proxy settings (corporate proxy/VPN)
    async with httpx.AsyncClient(
        base_url=settings.API_URL, timeout=5.0, trust_env=False
    ) as client:
        return await client.post(path, json=json, headers=headers)


# ---------------------------------------------------------------------------
# Test 1: Backend reachable
# ---------------------------------------------------------------------------

def test_backend_reachable():
    """
    DIAGNOSTIC: Can the simulator reach the backend at all?
    Fails with ConnectionError if backend is not running.
    """
    try:
        response = run(_get("/health"))
        assert response.status_code == 200, (
            f"Backend reachable but /health returned {response.status_code}: {response.text}"
        )
        data = response.json()
        assert data.get("status") == "ok", f"Unexpected health response: {data}"
    except httpx.ConnectError as e:
        pytest.fail(
            f"\n\n❌ BACKEND NOT REACHABLE at {settings.API_URL}\n"
            f"   Error: {e}\n\n"
            f"   Fix: Start the backend first:\n"
            f"     cd backend\n"
            f"     .venv\\Scripts\\activate\n"
            f"     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\n"
        )
    except httpx.ReadError as e:
        pytest.fail(
            f"\n\n❌ CONNECTION RESET at {settings.API_URL}\n"
            f"   Error: {type(e).__name__}: {e}\n\n"
            f"   Possible causes:\n"
            f"   - Backend crashed on startup (check uvicorn terminal)\n"
            f"   - Firewall or proxy blocking port 8000\n"
            f"   - IPv6/IPv4 mismatch: 'localhost' resolves to ::1 but backend on 127.0.0.1\n"
            f"     ✓ Already fixed: API_URL=http://127.0.0.1:8000 in simulator/.env\n"
            f"   - Corporate VPN/proxy intercepting local traffic\n"
            f"     Try: disable VPN, then rerun\n"
        )
    except Exception as e:
        pytest.fail(
            f"\n\n❌ UNEXPECTED ERROR connecting to {settings.API_URL}\n"
            f"   Error: {type(e).__name__}: {e}\n"
        )


# ---------------------------------------------------------------------------
# Test 2: Can post telemetry (unauthenticated)
# ---------------------------------------------------------------------------

def test_can_post_telemetry():
    """
    DIAGNOSTIC: Can the simulator post telemetry without authentication?
    This endpoint is special — it allows unauthenticated access for simulator.
    """
    # First get a machine ID (this still requires auth for now)
    try:
        # For testing purposes, we'll use a known machine ID or skip if not available
        # In production, simulator fetches machines at startup with auth
        payload = {
            "machine_id": "00000000-0000-0000-0000-000000000001",  # Test machine ID
            "sensor_type": "engine_temp",
            "value": 85.0,
            "unit": "celsius",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        response = run(_post("/telemetry", json=payload, token=None))  # No token!
    except (httpx.ConnectError, httpx.ReadError) as e:
        pytest.fail(f"Connection error posting telemetry: {e}")

    # Accept 201 (created) or 404 (machine not found - expected for test ID)
    # The important thing is we're NOT getting 401 Unauthorized
    assert response.status_code in (200, 201, 404), (
        f"POST /telemetry returned {response.status_code}: {response.text}\n"
        f"Expected 201 (success), 404 (machine not found), but got authentication error.\n"
        f"Telemetry endpoint should accept unauthenticated requests from simulator."
    )
    
    if response.status_code == 401:
        pytest.fail(
            f"\n\n❌ TELEMETRY ENDPOINT REQUIRES AUTH\n"
            f"   The telemetry endpoint should allow unauthenticated access for simulator.\n"
            f"   Check that backend dependencies.py has get_current_user_optional.\n"
        )
    
    print(f"\n✓ Telemetry endpoint accepts unauthenticated requests (status: {response.status_code})")


# ---------------------------------------------------------------------------
# Test 3: API token still required for other endpoints
# ---------------------------------------------------------------------------

def test_other_endpoints_require_auth():
    """
    DIAGNOSTIC: Verify that non-telemetry endpoints still require authentication.
    """
    try:
        response = run(_get("/machines", token=None))  # No token
    except (httpx.ConnectError, httpx.ReadError):
        pytest.skip("Backend not reachable")

    assert response.status_code == 401 or response.status_code == 403, (
        f"GET /machines without auth should return 401/403, got {response.status_code}\n"
        f"Other endpoints should still be protected!"
    )
    print(f"\n✓ Non-telemetry endpoints still require authentication (status: {response.status_code})")


# DEPRECATED TESTS - API_TOKEN removed from simulator
# ---------------------------------------------------------------------------

def test_api_token_removed():
    """
    DIAGNOSTIC: Verify API_TOKEN is no longer in settings (as intended).
    """
    assert not hasattr(settings, 'API_TOKEN'), (
        "API_TOKEN still exists in settings — it should be removed for simulator"
    )
    print("\n✓ API_TOKEN successfully removed from simulator config")


# ---------------------------------------------------------------------------
# Test 4: Map config still requires auth
# ---------------------------------------------------------------------------

def test_can_fetch_map_config():
    """
    DIAGNOSTIC: Map config endpoint should still require authentication.
    Note: In production, you'll need to handle auth for this endpoint.
    """
    try:
        response = run(_get("/map-config", token=None))
    except (httpx.ConnectError, httpx.ReadError):
        pytest.skip("Backend not reachable — run test_backend_reachable first")

    # Map config should require auth (401) or not exist (404)
    # Both are acceptable — we're just verifying it's not open
    assert response.status_code in (401, 403, 404), (
        f"GET /map-config without auth returned {response.status_code}\n"
        f"Expected 401/403/404 — this endpoint should be protected or not found"
    )

    print(
        f"\n✓ Map config endpoint protected or not configured (status: {response.status_code})"
    )
