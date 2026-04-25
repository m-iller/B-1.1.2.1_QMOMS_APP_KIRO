import asyncio
import json
import logging
import random
from datetime import datetime, timezone
from dataclasses import dataclass

import httpx

from simulator.api_client import ApiClient
from simulator.config import settings
from simulator.generators import (
    GENERATORS,
    compute_antenna_estimate,
    find_nearest_antenna,
    update_position,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SIM] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class QuarryBounds:
    center_lat: float
    center_lng: float
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float

    @classmethod
    def from_center(cls, lat: float, lng: float, radius: float) -> "QuarryBounds":
        return cls(
            center_lat=lat,
            center_lng=lng,
            min_lat=lat - radius,
            max_lat=lat + radius,
            min_lng=lng - radius,
            max_lng=lng + radius,
        )


async def fetch_machine_ids(client: ApiClient, interval_s: float) -> list[str]:
    """Fetch all machine IDs from API, retrying until at least one is found."""
    while True:
        try:
            machines = await client.get_machines()
            ids = [m["id"] for m in machines]
            if ids:
                logger.info(f"Found {len(ids)} machines: {ids}")
                return ids
            else:
                logger.warning("No machines found in DB. Retrying in %.1fs...", interval_s)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to fetch machines: HTTP {e.response.status_code} "
                f"{e.response.text[:200]}. Retrying in {interval_s}s..."
            )
        except Exception as e:
            logger.error(
                f"Failed to fetch machines: {type(e).__name__}: {e}. "
                f"Is backend running at {settings.API_URL}? Retrying in {interval_s}s..."
            )
        await asyncio.sleep(interval_s)


async def fetch_map_config(client: ApiClient, interval_s: float) -> tuple[QuarryBounds, list[dict]]:
    """
    Fetch map center and antennas from GET /map-config.
    Retries until map config is available — no hardcoded fallback.
    """
    while True:
        map_cfg = await client.get_map_config()
        if map_cfg and "center_lat" in map_cfg and "center_lng" in map_cfg:
            lat = map_cfg["center_lat"]
            lng = map_cfg["center_lng"]
            bounds = QuarryBounds.from_center(lat, lng, settings.POSITION_RADIUS)
            logger.info(
                f"Map center from API: ({lat:.6f}, {lng:.6f}) "
                f"bounds ±{settings.POSITION_RADIUS}°"
            )

            # Use antennas from map config if ANTENNAS_JSON not set
            antennas: list[dict] = []
            if settings.ANTENNAS_JSON.strip():
                try:
                    antennas = json.loads(settings.ANTENNAS_JSON)
                    logger.info(f"Using {len(antennas)} antennas from ANTENNAS_JSON env var")
                except Exception as e:
                    logger.error(f"Failed to parse ANTENNAS_JSON: {e}")

            if not antennas and map_cfg.get("antennas"):
                antennas = [
                    {"name": a["name"], "lat": a["lat"], "lng": a["lng"]}
                    for a in map_cfg["antennas"]
                ]
                logger.info(f"Using {len(antennas)} antennas from map config API: {[a['name'] for a in antennas]}")

            if not antennas:
                logger.warning("No antennas found in map config or ANTENNAS_JSON — position telemetry disabled")

            return bounds, antennas

        logger.warning(
            f"Map config not available from API — retrying in {interval_s}s. "
            f"Configure map via PUT /map-config or frontend Map View → Configure Map."
        )
        await asyncio.sleep(interval_s)


def scatter_near(bounds: QuarryBounds, init_radius: float = 0.01) -> tuple[float, float]:
    """Random position within init_radius of center, clamped to bounds."""
    lat = bounds.center_lat + random.uniform(-init_radius, init_radius)
    lng = bounds.center_lng + random.uniform(-init_radius, init_radius)
    lat = max(bounds.min_lat, min(bounds.max_lat, lat))
    lng = max(bounds.min_lng, min(bounds.max_lng, lng))
    return round(lat, 7), round(lng, 7)


async def run_simulation() -> None:
    client = ApiClient()
    interval_s = settings.INTERVAL_MS / 1000

    # Fetch map config from API — blocks until available
    logger.info("Fetching map configuration from API...")
    bounds, antennas = await fetch_map_config(client, interval_s)

    # Resolve machine IDs — use configured list or fetch all from DB
    if settings.MACHINE_IDS.strip():
        machine_ids = [m.strip() for m in settings.MACHINE_IDS.split(",") if m.strip()]
        logger.info(f"Using configured machine IDs ({len(machine_ids)}): {machine_ids}")
    else:
        logger.info("MACHINE_IDS not set — fetching all machines from DB...")
        machine_ids = await fetch_machine_ids(client, interval_s)

    # Scatter each machine within init_radius of map center
    positions: dict[str, tuple[float, float]] = {
        mid: scatter_near(bounds) for mid in machine_ids
    }
    logger.info(
        f"Starting simulation for {len(machine_ids)} machines at {interval_s}s intervals. "
        f"Center: ({bounds.center_lat:.6f}, {bounds.center_lng:.6f}), "
        f"radius: ±{settings.POSITION_RADIUS}°"
    )

    while True:
        for machine_id in machine_ids:
            # Advance true position via random walk, clamped to bounds
            lat, lng = positions.get(machine_id, (bounds.center_lat, bounds.center_lng))
            new_lat = lat + random.uniform(-0.0002, 0.0002)
            new_lng = lng + random.uniform(-0.0002, 0.0002)
            new_lat = max(bounds.min_lat, min(bounds.max_lat, new_lat))
            new_lng = max(bounds.min_lng, min(bounds.max_lng, new_lng))
            lat, lng = round(new_lat, 7), round(new_lng, 7)
            positions[machine_id] = (lat, lng)

            # --- Standard sensor telemetry ---
            for sensor_type, generator in GENERATORS.items():
                reading = generator()
                payload = {
                    "machine_id": machine_id,
                    "sensor_type": sensor_type,
                    "value": reading["value"],
                    "unit": reading["unit"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                try:
                    await client.post_telemetry(payload)
                    logger.debug(f"machine={machine_id} sensor={sensor_type} value={reading['value']}")
                except Exception as e:
                    logger.error(f"Error for machine={machine_id} sensor={sensor_type}: {e}")

            # --- Position telemetry (antenna-based estimate) ---
            if antennas:
                nearest = find_nearest_antenna(lat, lng, antennas)
                est_lat, est_lng = compute_antenna_estimate(lat, lng, settings.POSITION_NOISE_STD)
                antenna_name = nearest["name"]

                for sensor_type, value in [("pos_x", est_lng), ("pos_y", est_lat)]:
                    pos_payload = {
                        "machine_id": machine_id,
                        "sensor_type": sensor_type,
                        "value": value,
                        "unit": "degrees",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    try:
                        await client.post_telemetry(pos_payload)
                        logger.debug(
                            f"machine={machine_id} sensor={sensor_type} value={value:.6f} "
                            f"antenna={antenna_name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error for machine={machine_id} sensor={sensor_type} "
                            f"antenna={antenna_name}: {e}"
                        )

        await asyncio.sleep(interval_s)


def main() -> None:
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
