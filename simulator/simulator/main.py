import asyncio
import json
import logging
from datetime import datetime, timezone

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
    """Fetch machine IDs from API, retrying until at least one is found."""
    while True:
        try:
            machines = await client.get_machines()
            ids = [m["id"] for m in machines]
            if ids:
                logger.info(f"Found {len(ids)} machines: {ids}")
                return ids
            else:
                logger.warning("No machines found. Retrying in %.1fs...", interval_s)
        except Exception as e:
            import httpx
            if isinstance(e, httpx.HTTPStatusError):
                logger.error(
                    f"Failed to fetch machines: HTTP {e.response.status_code} "
                    f"{e.response.text[:200]}. Retrying in {interval_s}s..."
                )
            else:
                logger.error(f"Failed to fetch machines: {type(e).__name__}: {e}. Retrying in {interval_s}s...")
        await asyncio.sleep(interval_s)


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

    # Resolve machine IDs
    if settings.MACHINE_IDS:
        machine_ids = [m.strip() for m in settings.MACHINE_IDS.split(",") if m.strip()]
        logger.info(f"Using configured machine IDs: {machine_ids}")
    else:
        logger.info("Fetching machine IDs from API...")
        machine_ids = await fetch_machine_ids(client, interval_s)

    # Initialize positions at center of quarry bounding box
    center_lat = (settings.QUARRY_MIN_LAT + settings.QUARRY_MAX_LAT) / 2
    center_lng = (settings.QUARRY_MIN_LNG + settings.QUARRY_MAX_LNG) / 2
    positions: dict[str, tuple[float, float]] = {
        mid: (center_lat, center_lng) for mid in machine_ids
    }

    logger.info(
        f"Starting simulation for {len(machine_ids)} machines at {interval_s}s intervals. "
        f"Center: ({center_lat:.4f}, {center_lng:.4f})"
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

                # pos_x = longitude, pos_y = latitude (matches backend Machine.pos_x/pos_y)
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
