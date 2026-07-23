
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem


class Restaurant(Base):
    """Restaurant model representing a dining establishment."""

    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False
    )
    city: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )
    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )
    website: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
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

    # Relationships
    menu_items: Mapped[List["MenuItem"]] = relationship(
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

