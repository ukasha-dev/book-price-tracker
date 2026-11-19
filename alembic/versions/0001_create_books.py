"""create books table

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("availability", sa.String(length=100), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_url", name="uq_books_source_url"),
        sa.CheckConstraint("price >= 0", name="ck_books_price_non_negative"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_books_rating_range"),
    )
    op.create_index("ix_books_category", "books", ["category"])
    op.create_index("ix_books_price", "books", ["price"])


def downgrade() -> None:
    op.drop_index("ix_books_price", table_name="books")
    op.drop_index("ix_books_category", table_name="books")
    op.drop_table("books")
