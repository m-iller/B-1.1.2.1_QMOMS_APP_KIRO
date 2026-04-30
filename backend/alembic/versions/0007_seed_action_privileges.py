"""seed action privileges into role_permissions

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-30 00:00:00.000000
"""
import json
from typing import Sequence, Union
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Full permissions per role: pages + action privileges
ROLE_PERMISSIONS = {
    "operator": [
        "dashboard", "tasks",
        "tasks.create",
    ],
    "dispatcher": [
        "dashboard", "map", "tasks", "notifications", "analytics", "machinery", "zones", "routes",
        "tasks.create", "tasks.delete",
        "machines.edit_state", "machines.edit_config",
        "map.configure",
        "zones.create", "zones.delete",
        "routes.manage",
        "conflicts.resolve",
    ],
    "manager": [
        "dashboard", "analytics", "tasks", "notifications",
        "tasks.create",
    ],
    "admin": [
        "dashboard", "map", "tasks", "notifications", "analytics", "machinery", "zones", "routes",
        "tasks.create", "tasks.delete",
        "machines.edit_state", "machines.edit_config", "machines.delete",
        "map.configure",
        "zones.create", "zones.delete",
        "routes.manage",
        "conflicts.resolve",
    ],
    "mechanic": [
        "dashboard", "tasks",
        "tasks.create",
    ],
    "IT": ["dashboard"],
    "owner": ["dashboard", "analytics"],
    "dev": [
        "dashboard", "map", "tasks", "notifications", "analytics", "machinery", "zones", "routes", "roles",
        "tasks.create", "tasks.delete",
        "machines.edit_state", "machines.edit_config", "machines.delete",
        "map.configure",
        "zones.create", "zones.delete",
        "routes.manage",
        "conflicts.resolve",
    ],
}


def upgrade() -> None:
    for role, pages in ROLE_PERMISSIONS.items():
        pages_json = json.dumps(pages).replace("'", "''")
        op.execute(
            f"UPDATE role_permissions SET pages = '{pages_json}'::jsonb, "
            f"updated_at = NOW() WHERE role = '{role}'"
        )


def downgrade() -> None:
    pass  # No rollback — permissions are additive
