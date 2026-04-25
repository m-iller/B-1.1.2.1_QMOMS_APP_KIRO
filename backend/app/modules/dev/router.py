"""
DEV-ONLY endpoints — tagged DELETE_BEFORE_PROD.
These routes must be removed before any production deployment.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_roles
from app.modules.machine.models import Machine

router = APIRouter()

_SEED_FILE = Path(__file__).parent.parent.parent.parent / "data" / "seed_machines.json"


@router.post("/dev/reset-and-seed", tags=["DELETE_BEFORE_PROD"])
async def reset_and_seed(
    db: AsyncSession = Depends(get_db),
    _actor=Depends(require_roles(["dev"])),
):
    """
    DELETE_BEFORE_PROD
    Truncates all operational tables (cascades) and re-seeds machines
    from data/seed_machines.json. Leaves users intact.
    """
    # Truncate operational data — CASCADE handles FK children
    await db.execute(text(
        "TRUNCATE TABLE telemetry_data, machine_states, conflicts, tasks, "
        "task_dependencies, haul_cycles, events, notifications, reports, "
        "machines RESTART IDENTITY CASCADE"
    ))

    # Seed machines
    seed: list[dict] = json.loads(_SEED_FILE.read_text())
    machines = [
        Machine(name=m["name"], type=m["type"], current_state="idle")
        for m in seed
    ]
    db.add_all(machines)
    await db.commit()

    # Return created machine ids
    for m in machines:
        await db.refresh(m)

    return {
        "message": f"DB reset. {len(machines)} machines seeded.",
        "machines": [{"id": m.id, "name": m.name, "type": m.type} for m in machines],
    }
