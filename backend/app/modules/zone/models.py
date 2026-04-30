from sqlalchemy import Float, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

ZONE_TYPES = [
    "weighbridge", "fuel_station", "workshop", "stockpile",
    "dump_zone", "loading_zone", "crusher_station", "general",
]

ZONE_TYPE_COLORS: dict[str, str] = {
    "weighbridge":     "#8b5cf6",
    "fuel_station":    "#f59e0b",
    "workshop":        "#6b7280",
    "stockpile":       "#d97706",
    "dump_zone":       "#ef4444",
    "loading_zone":    "#10b981",
    "crusher_station": "#dc2626",
    "general":         "#3b82f6",
}


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    zone_type: Mapped[str | None] = mapped_column(nullable=True)
    color: Mapped[str | None] = mapped_column(nullable=True, server_default=text("'#3b82f6'"))
    # shape: 'circle' | 'rectangle' | 'polygon'
    shape: Mapped[str | None] = mapped_column(nullable=True, server_default=text("'circle'"))
    # circle fields
    center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_meters: Mapped[float | None] = mapped_column(Float, nullable=True, server_default=text("200"))
    # rectangle/polygon: [{lat, lng}, ...]
    polygon_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[str] = mapped_column(nullable=False, server_default=text("NOW()"))
    updated_at: Mapped[str] = mapped_column(nullable=False, server_default=text("NOW()"))
