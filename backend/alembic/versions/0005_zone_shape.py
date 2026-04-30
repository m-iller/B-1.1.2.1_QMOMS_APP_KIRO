"""add zone shape fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-30 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # shape: 'circle' | 'rectangle' | 'polygon'
    op.add_column("zones", sa.Column("shape", sa.VARCHAR(20), nullable=True, server_default="circle"))
    # polygon_points: [{lat, lng}, ...] — used for polygon and rectangle shapes
    op.add_column(
        "zones",
        sa.Column(
            "polygon_points",
            postgresql.JSONB(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("zones", "polygon_points")
    op.drop_column("zones", "shape")
