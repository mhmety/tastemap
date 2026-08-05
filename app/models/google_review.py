import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class GoogleReview(Base):
    __tablename__ = "google_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    author_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    review_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    review_date: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    profile_photo: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    likes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    provider_review_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    review_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    raw_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    restaurant: Mapped["Restaurant"] = relationship(
        back_populates="google_reviews",
    )

