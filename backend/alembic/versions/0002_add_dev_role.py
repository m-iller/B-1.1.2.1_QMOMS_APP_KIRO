"""add dev role

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-25 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old constraint and recreate with 'dev' included
    op.drop_constraint("ck_users_role", "users")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('operator','dispatcher','manager','admin','mechanic','IT','owner','dev')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users")
    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('operator','dispatcher','manager','admin','mechanic','IT','owner')",
    )
