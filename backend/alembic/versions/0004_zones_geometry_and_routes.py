"""add zone geometry and machine routes

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-30 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add geometry fields to zones
    op.add_column("zones", sa.Column("zone_type", sa.VARCHAR(50), nullable=True))
    op.add_column("zones", sa.Column("color", sa.VARCHAR(20), nullable=True, server_default="#3b82f6"))
    op.add_column("zones", sa.Column("center_lat", sa.Float(), nullable=True))
    op.add_column("zones", sa.Column("center_lng", sa.Float(), nullable=True))
    op.add_column("zones", sa.Column("radius_meters", sa.Float(), nullable=True, server_default="200"))

    # Machine routes table
    op.create_table(
        "machine_routes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("name", sa.VARCHAR(100), nullable=False, server_default="Route"),
        sa.Column(
            "waypoints",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "color",
            sa.VARCHAR(20),
            nullable=False,
            server_default="#ef4444",
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
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("machine_routes")
    op.drop_column("zones", "radius_meters")
    op.drop_column("zones", "center_lng")
    op.drop_column("zones", "center_lat")
    op.drop_column("zones", "color")
    op.drop_column("zones", "zone_type")
