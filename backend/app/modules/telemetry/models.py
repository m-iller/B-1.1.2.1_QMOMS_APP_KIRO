from sqlalchemy import Float, ForeignKey, PrimaryKeyConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelemetryData(Base):
    __tablename__ = "telemetry_data"
    __table_args__ = (PrimaryKeyConstraint("id", "timestamp"),)

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    machine_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("machines.id", ondelete="CASCADE"),
        nullable=False,
    )
    sensor_type: Mapped[str] = mapped_column(nullable=False)
    normalized_value: Mapped[float] = mapped_column(Float, nullable=False)
    canonical_unit: Mapped[str] = mapped_column(nullable=False)
    timestamp: Mapped[str] = mapped_column(nullable=False)


class Anomaly(Base):
    __tablename__ = "anomalies"

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
    telemetry_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    sensor_type: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
