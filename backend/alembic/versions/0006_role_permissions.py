"""add role_permissions table and remove role check constraint

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-30 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default page permissions per built-in role
DEFAULT_PERMISSIONS = [
    ("operator",   ["dashboard", "tasks"]),
    ("dispatcher", ["dashboard", "map", "tasks", "notifications", "analytics", "machinery", "zones", "routes"]),
    ("manager",    ["dashboard", "analytics", "tasks", "notifications"]),
    ("admin",      ["dashboard", "map", "tasks", "notifications", "analytics", "machinery", "zones", "routes"]),
    ("mechanic",   ["dashboard", "tasks"]),
    ("IT",         ["dashboard"]),
    ("owner",      ["dashboard", "analytics"]),
    ("dev",        ["dashboard", "map", "tasks", "notifications", "analytics", "machinery", "zones", "routes", "roles"]),
]


def upgrade() -> None:
    # Remove the role check constraint so custom roles can be created
    op.drop_constraint("ck_users_role", "users")

    # Create role_permissions table
    op.create_table(
        "role_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("role", sa.VARCHAR(50), nullable=False, unique=True),
        sa.Column(
            "pages",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed default permissions using proper JSON format
    for role, pages in DEFAULT_PERMISSIONS:
        import json
        pages_json = json.dumps(pages).replace("'", "''")
        op.execute(f"INSERT INTO role_permissions (role, pages) VALUES ('{role}', '{pages_json}'::jsonb)")


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('operator','dispatcher','manager','admin','mechanic','IT','owner','dev')",
    )
