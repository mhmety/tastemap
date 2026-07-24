
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.restaurant import Restaurant


class Favorite(Base):
    """Favorite model representing a user's favorite restaurant."""

    __tablename__ = "favorites"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Unique constraint to prevent duplicate favorites
    __table_args__ = (
        UniqueConstraint("user_id", "restaurant_id", name="uq_user_restaurant_favorite"),
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="favorites",
    )
    restaurant: Mapped["Restaurant"] = relationship(
        back_populates="favorites",
    )

