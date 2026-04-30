"""add machine description and enabled_sensors

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-30 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# All known sensor types — default when no config set
_DEFAULT_SENSORS = '["engine_temp","fuel_level","speed","payload_weight"]'


def upgrade() -> None:
    op.add_column(
        "machines",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "machines",
        sa.Column(
            "enabled_sensors",
            postgresql.JSONB(),
            nullable=False,
            server_default=_DEFAULT_SENSORS,
        ),
    )


def downgrade() -> None:
    op.drop_column("machines", "enabled_sensors")
    op.drop_column("machines", "description")
