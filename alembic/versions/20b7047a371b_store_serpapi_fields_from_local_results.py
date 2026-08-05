"""store serpapi fields from local_results

Revision ID: 20b7047a371b
Revises: d9589e4d32ff
Create Date: 2026-07-31 09:30:07.640659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20b7047a371b'
down_revision: Union[str, Sequence[str], None] = 'd9589e4d32ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("restaurants")}

    if "rating" not in existing:
        op.add_column("restaurants", sa.Column("rating", sa.Float(), nullable=True))
    if "review_count" not in existing:
        op.add_column("restaurants", sa.Column("review_count", sa.Integer(), nullable=True))
    if "category" not in existing:
        op.add_column("restaurants", sa.Column("category", sa.String(length=100), nullable=True))
    if "price_level" not in existing:
        op.add_column("restaurants", sa.Column("price_level", sa.String(length=20), nullable=True))
    if "opening_hours" not in existing:
        op.add_column("restaurants", sa.Column("opening_hours", sa.Text(), nullable=True))
    if "operating_hours" not in existing:
        op.add_column("restaurants", sa.Column("operating_hours", sa.JSON(), nullable=True))
    if "google_place_id" not in existing:
        op.add_column(
            "restaurants", sa.Column("google_place_id", sa.String(length=255), nullable=True)
        )
    if "serpapi_data_id" not in existing:
        op.add_column(
            "restaurants", sa.Column("serpapi_data_id", sa.String(length=255), nullable=True)
        )
    if "thumbnail" not in existing:
        op.add_column("restaurants", sa.Column("thumbnail", sa.String(length=500), nullable=True))
    if "reviews_link" not in existing:
        op.add_column("restaurants", sa.Column("reviews_link", sa.String(length=500), nullable=True))
    if "photos_link" not in existing:
        op.add_column("restaurants", sa.Column("photos_link", sa.String(length=500), nullable=True))
    if "user_review" not in existing:
        op.add_column("restaurants", sa.Column("user_review", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("restaurants")}

    if "user_review" in existing:
        op.drop_column("restaurants", "user_review")
    if "photos_link" in existing:
        op.drop_column("restaurants", "photos_link")
    if "reviews_link" in existing:
        op.drop_column("restaurants", "reviews_link")
    if "thumbnail" in existing:
        op.drop_column("restaurants", "thumbnail")
    if "serpapi_data_id" in existing:
        op.drop_column("restaurants", "serpapi_data_id")
    if "google_place_id" in existing:
        op.drop_column("restaurants", "google_place_id")
    if "operating_hours" in existing:
        op.drop_column("restaurants", "operating_hours")
    if "opening_hours" in existing:
        op.drop_column("restaurants", "opening_hours")
    if "price_level" in existing:
        op.drop_column("restaurants", "price_level")
    if "category" in existing:
        op.drop_column("restaurants", "category")
    if "review_count" in existing:
        op.drop_column("restaurants", "review_count")
    if "rating" in existing:
        op.drop_column("restaurants", "rating")
