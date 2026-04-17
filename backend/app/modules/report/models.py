from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    shift_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("shifts.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[str] = mapped_column(
        nullable=False, server_default=text("NOW()")
    )
