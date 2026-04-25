"""Seed script — inserts baseline data into the database.

Usage:
    python -m app.seed
"""

import asyncio
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import text

from app.database import AsyncSessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # ------------------------------------------------------------------
        # Users — one per role
        # ------------------------------------------------------------------
        roles = ["operator", "dispatcher", "manager", "admin", "mechanic", "IT", "owner", "dev"]
        user_ids: dict[str, str] = {}

        for role in roles:
            username = role.lower()
            password_hash = pwd_context.hash(f"{username}pass123")
            result = await db.execute(
                text(
                    "INSERT INTO users (username, password_hash, role) "
                    "VALUES (:username, :password_hash, :role) "
                    "ON CONFLICT (username) DO UPDATE SET role = EXCLUDED.role "
                    "RETURNING id"
                ),
                {"username": username, "password_hash": password_hash, "role": role},
            )
            user_id = result.scalar_one()
            user_ids[role] = str(user_id)
            print(f"  [users] upserted '{username}' (role={role})")

        # ------------------------------------------------------------------
        # Zones
        # ------------------------------------------------------------------
        zone_ids: list[str] = []
        for zone_name, zone_desc in [
            ("Zone A", "Primary excavation area"),
            ("Zone B", "Secondary loading area"),
        ]:
            result = await db.execute(
                text(
                    "INSERT INTO zones (name, description) "
                    "VALUES (:name, :description) "
                    "RETURNING id"
                ),
                {"name": zone_name, "description": zone_desc},
            )
            zone_id = str(result.scalar_one())
            zone_ids.append(zone_id)
            print(f"  [zones] inserted '{zone_name}' id={zone_id}")

        # ------------------------------------------------------------------
        # Machines
        # ------------------------------------------------------------------
        machines = [
            ("Excavator-01", "excavator"),
            ("HaulTruck-01", "haul_truck"),
            ("Drill-01", "drill"),
        ]
        for machine_name, machine_type in machines:
            result = await db.execute(
                text(
                    "INSERT INTO machines (name, type) "
                    "VALUES (:name, :type) "
                    "RETURNING id"
                ),
                {"name": machine_name, "type": machine_type},
            )
            machine_id = str(result.scalar_one())
            print(f"  [machines] inserted '{machine_name}' (type={machine_type}) id={machine_id}")

        # ------------------------------------------------------------------
        # Active shift
        # ------------------------------------------------------------------
        now = datetime.now(timezone.utc)
        result = await db.execute(
            text(
                "INSERT INTO shifts (name, start_time, active) "
                "VALUES (:name, :start_time, TRUE) "
                "RETURNING id"
            ),
            {"name": "Morning Shift", "start_time": now},
        )
        shift_id = str(result.scalar_one())
        print(f"  [shifts] inserted active shift id={shift_id}")

        await db.commit()
        print("\nSeed completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
