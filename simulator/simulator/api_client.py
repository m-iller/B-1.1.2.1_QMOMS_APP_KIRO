import httpx
from simulator.config import settings

class ApiClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.API_URL,
            headers={"Authorization": f"Bearer {settings.API_TOKEN}"},
            timeout=10.0,
        )

    async def post_telemetry(self, payload: dict) -> None:
        response = await self._client.post("/telemetry", json=payload)
        response.raise_for_status()

    async def get_machines(self) -> list[dict]:
        response = await self._client.get("/machines")
        response.raise_for_status()
        return response.json()

    async def aclose(self) -> None:
        await self._client.aclose()
