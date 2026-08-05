"""create_google_reviews_table

Revision ID: a9dcc939730a
Revises: 20b7047a371b
Create Date: 2026-07-31 21:11:50.944188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9dcc939730a'
down_revision: Union[str, Sequence[str], None] = '20b7047a371b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'google_reviews',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('restaurant_id', sa.UUID(), nullable=False),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('review_date', sa.String(length=100), nullable=True),
        sa.Column('profile_photo', sa.String(length=500), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('provider_review_id', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('review_hash', sa.String(length=64), nullable=False),
        sa.Column('raw_json', sa.JSON(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['restaurant_id'],
            ['restaurants.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_google_reviews_restaurant_id'),
        'google_reviews',
        ['restaurant_id'],
        unique=False,
    )
    op.create_index(
        op.f('uq_google_reviews_restaurant_id_provider_review_id'),
        'google_reviews',
        ['restaurant_id', 'provider_review_id'],
        unique=True,
    )
    op.create_index(
        op.f('uq_google_reviews_restaurant_id_review_hash'),
        'google_reviews',
        ['restaurant_id', 'review_hash'],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f('uq_google_reviews_restaurant_id_review_hash'),
        table_name='google_reviews',
    )
    op.drop_index(
        op.f('uq_google_reviews_restaurant_id_provider_review_id'),
        table_name='google_reviews',
    )
    op.drop_index(
        op.f('ix_google_reviews_restaurant_id'),
        table_name='google_reviews',
    )
    op.drop_table('google_reviews')
