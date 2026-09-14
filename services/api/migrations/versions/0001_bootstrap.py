"""Enable pgvector for the HireIn data layer.

Revision ID: 0001_bootstrap
Revises:
"""
from typing import Sequence

from alembic import op

revision: str = "0001_bootstrap"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # The extension may be shared by future objects. Avoid destructive automatic removal.
    pass
