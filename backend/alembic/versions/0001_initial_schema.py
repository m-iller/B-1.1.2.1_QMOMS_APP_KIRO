"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")

    # 1. users
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("username", sa.VARCHAR(100), nullable=False),
        sa.Column("password_hash", sa.VARCHAR(255), nullable=False),
        sa.Column(
            "role",
            sa.VARCHAR(50),
            nullable=False,
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
        sa.UniqueConstraint("username"),
        sa.CheckConstraint(
            "role IN ('operator','dispatcher','manager','admin','mechanic','IT','owner')",
            name="ck_users_role",
        ),
    )

    # 2. shifts
    op.create_table(
        "shifts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(100), nullable=False),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "active",
            sa.Boolean(),
            server_default=sa.text("TRUE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. zones
    op.create_table(
        "zones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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

    # 4. machines
    op.create_table(
        "machines",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(100), nullable=False),
        sa.Column("type", sa.VARCHAR(50), nullable=False),
        sa.Column(
            "current_state",
            sa.VARCHAR(50),
            server_default=sa.text("'idle'"),
            nullable=False,
        ),
        sa.Column(
            "conflict_active",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_dispatcher_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column(
            "current_zone_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column("pos_x", sa.Float(), nullable=True),
        sa.Column("pos_y", sa.Float(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["assigned_dispatcher_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["current_zone_id"], ["zones.id"], ondelete="SET NULL"
        ),
    )

    # 5. machine_states
    op.create_table(
        "machine_states",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("state", sa.VARCHAR(50), nullable=False),
        sa.Column("source", sa.VARCHAR(20), nullable=False),
        sa.Column(
            "set_by_user_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["set_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "source IN ('dispatcher','telemetry','operator')",
            name="ck_machine_states_source",
        ),
    )

    # 6. conflicts
    op.create_table(
        "conflicts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("dispatcher_state", sa.VARCHAR(50), nullable=False),
        sa.Column("operator_state", sa.VARCHAR(50), nullable=False),
        sa.Column(
            "resolved",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "resolved_by_user_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )

    # 7. telemetry_data (composite PK for TimescaleDB hypertable)
    op.create_table(
        "telemetry_data",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("sensor_type", sa.VARCHAR(50), nullable=False),
        sa.Column("normalized_value", sa.Float(), nullable=False),
        sa.Column("canonical_unit", sa.VARCHAR(20), nullable=False),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", "timestamp"),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="CASCADE"
        ),
    )

    # Convert telemetry_data to TimescaleDB hypertable
    op.execute(
        "SELECT create_hypertable('telemetry_data', 'timestamp', if_not_exists => TRUE)"
    )

    # Index for efficient time-range queries per machine/sensor
    op.create_index(
        "ix_telemetry_machine_sensor_time",
        "telemetry_data",
        ["machine_id", "sensor_type", sa.text("timestamp DESC")],
    )

    # 8. anomalies
    op.create_table(
        "anomalies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("telemetry_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("sensor_type", sa.VARCHAR(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="CASCADE"
        ),
    )

    # 9. tasks
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.VARCHAR(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.VARCHAR(20), nullable=False),
        sa.Column(
            "state",
            sa.VARCHAR(20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("deadline", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "pending_activation",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=False),
            nullable=True,
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
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high','critical')",
            name="ck_tasks_priority",
        ),
        sa.CheckConstraint(
            "state IN ('pending','active','completed','validated')",
            name="ck_tasks_state",
        ),
    )

    # 10. task_dependencies
    op.create_table(
        "task_dependencies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "depends_on_task_id", postgresql.UUID(as_uuid=False), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["depends_on_task_id"], ["tasks.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("task_id", "depends_on_task_id"),
    )

    # 11. haul_cycles
    op.create_table(
        "haul_cycles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("machine_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("origin_zone_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "destination_zone_id", postgresql.UUID(as_uuid=False), nullable=False
        ),
        sa.Column("payload_tonnes", sa.Float(), nullable=False),
        sa.Column(
            "status",
            sa.VARCHAR(20),
            server_default=sa.text("'in_progress'"),
            nullable=False,
        ),
        sa.Column(
            "immutable",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["origin_zone_id"], ["zones.id"]),
        sa.ForeignKeyConstraint(["destination_zone_id"], ["zones.id"]),
        sa.CheckConstraint(
            "status IN ('in_progress','completed')",
            name="ck_haul_cycles_status",
        ),
    )

    # 12. events
    op.create_table(
        "events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "machine_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column("event_type", sa.VARCHAR(50), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column(
            "expired",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["shift_id"], ["shifts.id"], ondelete="SET NULL"
        ),
    )

    # 13. reports
    op.create_table(
        "reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "generated_by",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column("data", postgresql.JSONB(), nullable=False),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["generated_by"], ["users.id"], ondelete="SET NULL"
        ),
    )

    # 14. notifications
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("type", sa.VARCHAR(20), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "read",
            sa.Boolean(),
            server_default=sa.text("FALSE"),
            nullable=False,
        ),
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=False),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["shift_id"], ["shifts.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "type IN ('alert','conflict','system')",
            name="ck_notifications_type",
        ),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("reports")
    op.drop_table("events")
    op.drop_table("haul_cycles")
    op.drop_table("task_dependencies")
    op.drop_table("tasks")
    op.drop_table("anomalies")
    op.drop_index("ix_telemetry_machine_sensor_time", table_name="telemetry_data")
    op.drop_table("telemetry_data")
    op.drop_table("conflicts")
    op.drop_table("machine_states")
    op.drop_table("machines")
    op.drop_table("zones")
    op.drop_table("shifts")
    op.drop_table("users")
