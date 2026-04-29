import asyncio
import json
import logging
import random
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from pathlib import Path

import httpx

from simulator.api_client import ApiClient
from simulator.config import settings
from simulator.generators import (
    GENERATORS,
    compute_antenna_estimate,
    find_nearest_antenna,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SIM] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Machine states and task data
# ---------------------------------------------------------------------------

MACHINE_STATES = ["idle", "operating", "maintenance", "breakdown"]

# Loop timing multipliers — relative to base telemetry interval
STATE_LOOP_INTERVAL_MULTIPLIER = 3   # state changes 3x less frequent than telemetry
TASK_LOOP_INTERVAL_MULTIPLIER = 2    # task events 2x less frequent than telemetry

# Task state progression: pending → active → completed
TASK_NEXT_STATE: dict[str, str] = {
    "pending": "active",
    "active": "completed",
}

_TASKS_FILE = Path(__file__).parent / "tasks.json"
try:
    TASK_TEMPLATES: list[dict] = json.loads(_TASKS_FILE.read_text())
    logger.info(f"Loaded {len(TASK_TEMPLATES)} task templates from {_TASKS_FILE.name}")
except Exception as exc:
    logger.warning(f"Could not load tasks.json ({exc}), using fallback task list")
    TASK_TEMPLATES = [
        {"title": "Perform safety check", "description": "Pre-shift safety inspection.", "priority": "high"},
        {"title": "Refuel machine", "description": "Top up fuel tank.", "priority": "medium"},
    ]


# ---------------------------------------------------------------------------
# Quarry bounds
# ---------------------------------------------------------------------------

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
            center_lat=lat, center_lng=lng,
            min_lat=lat - radius, max_lat=lat + radius,
            min_lng=lng - radius, max_lng=lng + radius,
        )


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

async def fetch_machine_ids(client: ApiClient, interval_s: float) -> list[str]:
    while True:
        try:
            machines = await client.get_machines()
            ids = [m["id"] for m in machines]
            if ids:
                logger.info(f"Found {len(ids)} machines: {ids}")
                return ids
            logger.warning("No machines in DB. Retrying in %.1fs...", interval_s)
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch machines: HTTP {e.response.status_code}. Retrying...")
        except Exception as e:
            logger.error(f"Failed to fetch machines: {type(e).__name__}: {e}. Is backend running at {settings.API_URL}?")
        await asyncio.sleep(interval_s)


async def fetch_map_config(client: ApiClient, interval_s: float) -> tuple[QuarryBounds, list[dict]]:
    while True:
        map_cfg = await client.get_map_config()
        if map_cfg and "center_lat" in map_cfg:
            lat, lng = map_cfg["center_lat"], map_cfg["center_lng"]
            bounds = QuarryBounds.from_center(lat, lng, settings.POSITION_RADIUS)
            logger.info(f"Map center from API: ({lat:.6f}, {lng:.6f}) bounds ±{settings.POSITION_RADIUS}°")

            antennas: list[dict] = []
            if settings.ANTENNAS_JSON.strip():
                try:
                    antennas = json.loads(settings.ANTENNAS_JSON)
                except Exception as e:
                    logger.error(f"Failed to parse ANTENNAS_JSON: {e}")
            if not antennas and map_cfg.get("antennas"):
                antennas = [{"name": a["name"], "lat": a["lat"], "lng": a["lng"]} for a in map_cfg["antennas"]]
                logger.info(f"Using {len(antennas)} antennas from map config API")
            return bounds, antennas

        logger.warning(f"Map config not available — retrying in {interval_s}s.")
        await asyncio.sleep(interval_s)


def scatter_near(bounds: QuarryBounds, radius: float = 0.01) -> tuple[float, float]:
    lat = bounds.center_lat + random.uniform(-radius, radius)
    lng = bounds.center_lng + random.uniform(-radius, radius)
    return (
        round(max(bounds.min_lat, min(bounds.max_lat, lat)), 7),
        round(max(bounds.min_lng, min(bounds.max_lng, lng)), 7),
    )


# ---------------------------------------------------------------------------
# Simulation loops
# ---------------------------------------------------------------------------

async def simulate_telemetry_and_position(
    client: ApiClient,
    machine_ids: list[str],
    bounds: QuarryBounds,
    antennas: list[dict],
    interval_s: float,
) -> None:
    """Continuously sends sensor telemetry and position updates."""
    positions: dict[str, tuple[float, float]] = {
        mid: scatter_near(bounds) for mid in machine_ids
    }
    logger.info(f"Telemetry loop started for {len(machine_ids)} machines")

    while True:
        for machine_id in machine_ids:
            lat, lng = positions.get(machine_id, (bounds.center_lat, bounds.center_lng))
            # Random walk clamped to bounds
            lat = round(max(bounds.min_lat, min(bounds.max_lat, lat + random.uniform(-0.0002, 0.0002))), 7)
            lng = round(max(bounds.min_lng, min(bounds.max_lng, lng + random.uniform(-0.0002, 0.0002))), 7)
            positions[machine_id] = (lat, lng)

            # Standard sensors
            for sensor_type, generator in GENERATORS.items():
                reading = generator()
                try:
                    await client.post_telemetry({
                        "machine_id": machine_id,
                        "sensor_type": sensor_type,
                        "value": reading["value"],
                        "unit": reading["unit"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Telemetry error machine={machine_id} sensor={sensor_type}: {e}")

            # Position telemetry
            if antennas:
                nearest = find_nearest_antenna(lat, lng, antennas)
                est_lat, est_lng = compute_antenna_estimate(lat, lng, settings.POSITION_NOISE_STD)
                for sensor_type, value in [("pos_x", est_lng), ("pos_y", est_lat)]:
                    try:
                        await client.post_telemetry({
                            "machine_id": machine_id,
                            "sensor_type": sensor_type,
                            "value": value,
                            "unit": "degrees",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    except Exception as e:
                        logger.error(f"Position error machine={machine_id} sensor={sensor_type}: {e}")

        await asyncio.sleep(interval_s)


async def simulate_machine_states(
    client: ApiClient,
    machine_ids: list[str],
    interval_s: float,
) -> None:
    """Randomly changes machine states at a low probability per tick."""
    logger.info(f"State simulation loop started (prob={settings.STATE_CHANGE_PROB}/tick)")

    # Track current simulated state per machine
    machine_states: dict[str, str] = {mid: "idle" for mid in machine_ids}

    while True:
        await asyncio.sleep(interval_s * STATE_LOOP_INTERVAL_MULTIPLIER)

        for machine_id in machine_ids:
            if random.random() > settings.STATE_CHANGE_PROB:
                continue

            current = machine_states.get(machine_id, "idle")
            new_state = random.choice(MACHINE_STATES)

            if new_state == current:
                continue

            try:
                await client.patch_machine_state(machine_id, new_state)
                machine_states[machine_id] = new_state
                logger.info(f"State change: machine={machine_id} {current} → {new_state}")
            except Exception as e:
                logger.error(f"State change error machine={machine_id}: {e}")


async def simulate_tasks(
    client: ApiClient,
    machine_ids: list[str],
    interval_s: float,
) -> None:
    """Randomly creates tasks and advances their states."""
    logger.info(
        f"Task simulation loop started "
        f"(create_prob={settings.TASK_CREATE_PROB}, advance_prob={settings.TASK_ADVANCE_PROB})"
    )

    # Track active task IDs per machine: {machine_id: [task_id, ...]}
    machine_tasks: dict[str, list[str]] = {mid: [] for mid in machine_ids}

    while True:
        await asyncio.sleep(interval_s * TASK_LOOP_INTERVAL_MULTIPLIER)

        for machine_id in machine_ids:
            active_tasks = machine_tasks[machine_id]

            # --- Advance existing tasks ---
            still_active = []
            for task_id in active_tasks:
                if random.random() > settings.TASK_ADVANCE_PROB:
                    still_active.append(task_id)
                    continue
                try:
                    # Fetch current state
                    tasks = await client.get_tasks(machine_id)
                    task = next((t for t in tasks if t["id"] == task_id), None)
                    if not task:
                        continue  # task gone
                    current_state = task["state"]
                    next_state = TASK_NEXT_STATE.get(current_state)
                    if next_state:
                        await client.update_task_state(task_id, next_state)
                        logger.info(f"Task advanced: machine={machine_id} task={task_id[:8]} {current_state}→{next_state}")
                        if next_state != "completed":
                            still_active.append(task_id)
                        # completed tasks drop out of tracking
                    else:
                        still_active.append(task_id)
                except Exception as e:
                    logger.error(f"Task advance error machine={machine_id} task={task_id[:8]}: {e}")
                    still_active.append(task_id)

            machine_tasks[machine_id] = still_active

            # --- Create new task ---
            if (
                random.random() < settings.TASK_CREATE_PROB
                and len(active_tasks) < settings.TASK_MAX_PER_MACHINE
            ):
                deadline = (datetime.now(timezone.utc) + timedelta(hours=random.randint(1, 8))).isoformat()
                template = random.choice(TASK_TEMPLATES)
                payload = {
                    "machine_id": machine_id,
                    "title": template["title"],
                    "description": template["description"],
                    "priority": template["priority"],
                    "deadline": deadline,
                }
                try:
                    task = await client.create_task(payload)
                    task_id = task["id"]
                    machine_tasks[machine_id].append(task_id)
                    logger.info(
                        f"Task created: machine={machine_id} task={task_id[:8]} "
                        f"'{payload['title']}' priority={payload['priority']}"
                    )
                except Exception as e:
                    logger.error(f"Task create error machine={machine_id}: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def run_simulation() -> None:
    client = ApiClient()
    interval_s = settings.INTERVAL_MS / 1000

    logger.info("Fetching map configuration from API...")
    bounds, antennas = await fetch_map_config(client, interval_s)

    if settings.MACHINE_IDS.strip():
        machine_ids = [m.strip() for m in settings.MACHINE_IDS.split(",") if m.strip()]
        logger.info(f"Using configured machine IDs ({len(machine_ids)}): {machine_ids}")
    else:
        logger.info("MACHINE_IDS not set — fetching all machines from DB...")
        machine_ids = await fetch_machine_ids(client, interval_s)

    logger.info(
        f"Starting simulation for {len(machine_ids)} machines. "
        f"Center: ({bounds.center_lat:.6f}, {bounds.center_lng:.6f})"
    )

    # Run all simulation loops concurrently
    await asyncio.gather(
        simulate_telemetry_and_position(client, machine_ids, bounds, antennas, interval_s),
        simulate_machine_states(client, machine_ids, interval_s),
        simulate_tasks(client, machine_ids, interval_s),
    )


def main() -> None:
    asyncio.run(run_simulation())


if __name__ == "__main__":
    main()
