"""add unique user restaurant review

Revision ID: c3e6c3a7e8d1
Revises: 0707ec78a5a7, a9dcc939730a
Create Date: 2026-08-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "c3e6c3a7e8d1"
down_revision: Union[str, Sequence[str], None] = ("0707ec78a5a7", "a9dcc939730a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_reviews_user_id_restaurant_id",
        "reviews",
        ["user_id", "restaurant_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_reviews_user_id_restaurant_id",
        "reviews",
        type_="unique",
    )

