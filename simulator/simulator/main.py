import asyncio
import json
import logging
import random
from datetime import datetime, timezone

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


async def fetch_map_center(client: ApiClient) -> tuple[float, float]:
    """
    Fetch map center from GET /map-config.
    Falls back to bounding box center if not configured or unreachable.
    """
    map_cfg = await client.get_map_config()
    if map_cfg and "center_lat" in map_cfg and "center_lng" in map_cfg:
        lat = map_cfg["center_lat"]
        lng = map_cfg["center_lng"]
        logger.info(f"Map center from API: ({lat:.4f}, {lng:.4f})")
        return lat, lng

    # Fallback: midpoint of bounding box
    lat = (settings.QUARRY_MIN_LAT + settings.QUARRY_MAX_LAT) / 2
    lng = (settings.QUARRY_MIN_LNG + settings.QUARRY_MAX_LNG) / 2
    logger.warning(f"Map config not available — using bounding box center: ({lat:.4f}, {lng:.4f})")
    return lat, lng


def scatter_near(center_lat: float, center_lng: float, radius: float = 0.01) -> tuple[float, float]:
    """
    Return a random position within `radius` degrees of center.
    radius=0.01 ≈ 1.1km — machines start spread near the map center.
    Max allowed deviation from center is 0.05 degrees.
    """
    lat = center_lat + random.uniform(-radius, radius)
    lng = center_lng + random.uniform(-radius, radius)
    # Clamp to ±0.05 from center (hard limit)
    lat = max(center_lat - 0.05, min(center_lat + 0.05, lat))
    lng = max(center_lng - 0.05, min(center_lng + 0.05, lng))
    # Also clamp to quarry bounds
    lat = max(settings.QUARRY_MIN_LAT, min(settings.QUARRY_MAX_LAT, lat))
    lng = max(settings.QUARRY_MIN_LNG, min(settings.QUARRY_MAX_LNG, lng))
    return round(lat, 7), round(lng, 7)


async def run_simulation() -> None:
    client = ApiClient()
    interval_s = settings.INTERVAL_MS / 1000

    # Parse antenna definitions
    try:
        antennas: list[dict] = json.loads(settings.ANTENNAS_JSON)
        logger.info(f"Loaded {len(antennas)} antennas: {[a['name'] for a in antennas]}")
    except Exception as e:
        logger.error(f"Failed to parse ANTENNAS_JSON: {e}. Using empty antenna list.")
        antennas = []

    # Resolve machine IDs — use configured list or fetch all from DB
    if settings.MACHINE_IDS.strip():
        machine_ids = [m.strip() for m in settings.MACHINE_IDS.split(",") if m.strip()]
        logger.info(f"Using configured machine IDs ({len(machine_ids)}): {machine_ids}")
    else:
        logger.info("MACHINE_IDS not set — fetching all machines from DB...")
        machine_ids = await fetch_machine_ids(client, interval_s)

    # Fetch map center from API to initialize positions near it
    center_lat, center_lng = await fetch_map_center(client)

    # Scatter each machine randomly within ~220m of map center
    positions: dict[str, tuple[float, float]] = {
        mid: scatter_near(center_lat, center_lng) for mid in machine_ids
    }
    logger.info(
        f"Starting simulation for {len(machine_ids)} machines at {interval_s}s intervals. "
        f"Positions initialized near ({center_lat:.4f}, {center_lng:.4f})"
    )

    while True:
        for machine_id in machine_ids:
            # Advance true position via random walk
            lat, lng = positions.get(machine_id, (center_lat, center_lng))
            lat, lng = update_position(lat, lng, settings)
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

                # pos_x = longitude, pos_y = latitude
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
            else:
                logger.warning("No antennas configured — skipping position telemetry")

        await asyncio.sleep(interval_s)


def main() -> None:
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
