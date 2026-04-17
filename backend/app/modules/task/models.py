from sqlalchemy import Boolean, Float, ForeignKey, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

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
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'pending'")
    )
    deadline: Mapped[str] = mapped_column(nullable=False)
    pending_activation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
    updated_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (UniqueConstraint("task_id", "depends_on_task_id"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    depends_on_task_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )


class HaulCycle(Base):
    __tablename__ = "haul_cycles"

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
    origin_zone_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("zones.id"),
        nullable=False,
    )
    destination_zone_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("zones.id"),
        nullable=False,
    )
    payload_tonnes: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        nullable=False, server_default=text("'in_progress'")
    )
    immutable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    start_time: Mapped[str] = mapped_column(nullable=False)
    end_time: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
