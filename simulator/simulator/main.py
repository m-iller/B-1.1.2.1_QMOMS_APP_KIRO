import asyncio
import logging
from datetime import datetime, timezone

from simulator.api_client import ApiClient
from simulator.config import settings
from simulator.generators import GENERATORS, update_position

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SIM] %(message)s")
logger = logging.getLogger(__name__)


async def run_simulation() -> None:
    client = ApiClient()
    interval_s = settings.INTERVAL_MS / 1000

    # Resolve machine IDs
    machine_ids: list[str] = []
    if settings.MACHINE_IDS:
        machine_ids = [m.strip() for m in settings.MACHINE_IDS.split(",") if m.strip()]
    else:
        logger.info("Fetching machine IDs from API...")
        try:
            machines = await client.get_machines()
            machine_ids = [m["id"] for m in machines]
            logger.info(f"Found {len(machine_ids)} machines: {machine_ids}")
        except Exception as e:
            logger.error(f"Failed to fetch machines: {e}. Retrying in {interval_s}s...")
            await asyncio.sleep(interval_s)

    # Track positions per machine
    positions: dict[str, tuple[float, float]] = {mid: (400.0, 250.0) for mid in machine_ids}

    logger.info(f"Starting simulation for {len(machine_ids)} machines at {interval_s}s intervals")

    while True:
        for machine_id in machine_ids:
            # Update position
            pos_x, pos_y = positions.get(machine_id, (400.0, 250.0))
            pos_x, pos_y = update_position(pos_x, pos_y)
            positions[machine_id] = (pos_x, pos_y)

            # Send telemetry for each sensor type
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
                    # Never crash — continue to next sensor/machine

        await asyncio.sleep(interval_s)


def main() -> None:
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
