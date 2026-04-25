import httpx
from simulator.config import settings


class ApiClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.API_URL,
            headers={"Authorization": f"Bearer {settings.API_TOKEN}"},
            timeout=10.0,
            trust_env=False,  # bypass system proxy (corporate VPN/proxy)
        )

    async def post_telemetry(self, payload: dict) -> None:
        response = await self._client.post("/telemetry", json=payload)
        response.raise_for_status()

    async def get_machines(self) -> list[dict]:
        response = await self._client.get("/machines")
        response.raise_for_status()
        return response.json()

    async def get_map_config(self) -> dict | None:
        """Fetch map config for center lat/lng. Returns None if not configured."""
        try:
            response = await self._client.get("/map-config")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    async def aclose(self) -> None:
        await self._client.aclose()
