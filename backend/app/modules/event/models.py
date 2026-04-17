from sqlalchemy import Boolean, ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(nullable=False)
    start_time: Mapped[str] = mapped_column(nullable=False)
    end_time: Mapped[str | None] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("TRUE")
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    machine_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("machines.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    shift_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("shifts.id", ondelete="SET NULL"),
        nullable=True,
    )
    expired: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("FALSE")
    )
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
