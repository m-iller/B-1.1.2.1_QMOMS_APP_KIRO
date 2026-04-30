from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# All sensor types the simulator can produce
ALL_SENSOR_TYPES: list[str] = ["engine_temp", "fuel_level", "speed", "payload_weight"]


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_state: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'idle'")
    )
    conflict_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    enabled_sensors: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text('\'["engine_temp","fuel_level","speed","payload_weight"]\''),
    )
    assigned_dispatcher_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_zone_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("zones.id", ondelete="SET NULL"),
        nullable=True,
    )
    pos_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    pos_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )


class MachineState(Base):
    __tablename__ = "machine_states"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(nullable=False)
    source: Mapped[str] = mapped_column(nullable=False)
    set_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )


class Conflict(Base):
    __tablename__ = "conflicts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
    )
    dispatcher_state: Mapped[str] = mapped_column(nullable=False)
    operator_state: Mapped[str] = mapped_column(nullable=False)
    resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    resolved_by_user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
