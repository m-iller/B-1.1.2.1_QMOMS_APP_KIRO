"""
Connectivity diagnostic tests for the simulator → backend connection.

Run with:
    cd simulator
    pytest tests/test_connectivity.py -v

These tests hit the REAL backend at API_URL from simulator/.env.
They are diagnostic — they tell you exactly what is wrong.
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
# Test 2: API token valid
# ---------------------------------------------------------------------------

def test_api_token_valid():
    """
    DIAGNOSTIC: Is the API_TOKEN in simulator/.env valid and not expired?
    """
    try:
        response = run(_get("/auth/me", token=settings.API_TOKEN))
    except (httpx.ConnectError, httpx.ReadError):
        pytest.skip("Backend not reachable — run test_backend_reachable first")

    if response.status_code == 401:
        pytest.fail(
            f"\n\n❌ API TOKEN INVALID OR EXPIRED\n"
            f"   Status: {response.status_code}\n"
            f"   Response: {response.text}\n\n"
            f"   Fix: Get a fresh token:\n"
            f"     POST {settings.API_URL}/auth/login\n"
            f"     Body: {{\"username\": \"dispatcher\", \"password\": \"dispatcherpass123\"}}\n"
            f"   Then update API_TOKEN in simulator/.env\n"
        )

    assert response.status_code == 200, (
        f"Unexpected status {response.status_code}: {response.text}\n"
        + (
            "\n   502 Bad Gateway = proxy/nginx intercepting request.\n"
            "   Try: API_URL=http://127.0.0.1:8000 in simulator/.env\n"
            "   Or disable VPN/corporate proxy.\n"
            if response.status_code == 502 else ""
        )
    )
    data = response.json()
    assert "role" in data, f"Unexpected /auth/me response: {data}"
    print(f"\n✓ Token valid — logged in as '{data.get('username')}' (role: {data.get('role')})")


# ---------------------------------------------------------------------------
# Test 3: Can fetch machines
# ---------------------------------------------------------------------------

def test_can_fetch_machines():
    """
    DIAGNOSTIC: Can the simulator fetch the machine list?
    """
    try:
        response = run(_get("/machines", token=settings.API_TOKEN))
    except (httpx.ConnectError, httpx.ReadError):
        pytest.skip("Backend not reachable — run test_backend_reachable first")

    if response.status_code == 401:
        pytest.fail(
            f"\n\n❌ UNAUTHORIZED fetching machines — token invalid or expired\n"
            f"   Run test_api_token_valid for details\n"
        )

    assert response.status_code == 200, (
        f"GET /machines returned {response.status_code}: {response.text}"
    )

    machines = response.json()
    assert isinstance(machines, list), f"Expected list, got: {type(machines)}"

    if len(machines) == 0:
        pytest.fail(
            f"\n\n⚠ NO MACHINES IN DATABASE\n"
            f"   Simulator has nothing to simulate.\n\n"
            f"   Fix: Run the seed script:\n"
            f"     cd backend\n"
            f"     python -m app.seed\n"
        )

    print(f"\n✓ Found {len(machines)} machine(s): {[m['name'] for m in machines]}")


# ---------------------------------------------------------------------------
# Test 4: Can post telemetry
# ---------------------------------------------------------------------------

def test_can_post_telemetry():
    """
    DIAGNOSTIC: Can the simulator post a telemetry reading?
    Uses the first machine from the DB.
    """
    try:
        machines_resp = run(_get("/machines", token=settings.API_TOKEN))
    except (httpx.ConnectError, httpx.ReadError):
        pytest.skip("Backend not reachable — run test_backend_reachable first")

    if machines_resp.status_code != 200 or not machines_resp.json():
        pytest.skip("No machines available — run test_can_fetch_machines first")

    machine_id = machines_resp.json()[0]["id"]

    payload = {
        "machine_id": machine_id,
        "sensor_type": "engine_temp",
        "value": 85.0,
        "unit": "celsius",
        "timestamp": "2026-01-01T00:00:00+00:00",
    }

    try:
        response = run(_post("/telemetry", json=payload, token=settings.API_TOKEN))
    except (httpx.ConnectError, httpx.ReadError) as e:
        pytest.fail(f"Connection error posting telemetry: {e}")

    assert response.status_code in (200, 201), (
        f"POST /telemetry returned {response.status_code}: {response.text}"
    )
    print(f"\n✓ Telemetry posted successfully for machine {machine_id}")


# ---------------------------------------------------------------------------
# Test 5: Can fetch map config
# ---------------------------------------------------------------------------

def test_can_fetch_map_config():
    """
    DIAGNOSTIC: Is map config available? (needed for position initialization)
    """
    try:
        response = run(_get("/map-config", token=settings.API_TOKEN))
    except (httpx.ConnectError, httpx.ReadError):
        pytest.skip("Backend not reachable — run test_backend_reachable first")

    if response.status_code == 404:
        pytest.fail(
            f"\n\n⚠ MAP CONFIG NOT FOUND\n"
            f"   Simulator will use bounding box center instead of map center.\n\n"
            f"   Fix: Create map config via PUT /map-config or use the frontend Map View → Configure Map\n"
            f"   Or create backend/data/map_config.json manually.\n"
        )

    assert response.status_code == 200, (
        f"GET /map-config returned {response.status_code}: {response.text}"
    )

    cfg = response.json()
    print(
        f"\n✓ Map config found — center: ({cfg.get('center_lat')}, {cfg.get('center_lng')}), "
        f"zoom: {cfg.get('default_zoom')}, "
        f"antennas: {len(cfg.get('antennas', []))}"
    )
