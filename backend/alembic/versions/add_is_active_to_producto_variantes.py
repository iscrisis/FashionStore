"""Add is_active column to producto_variantes

Revision ID: fix_producto_variantes_is_active
Revises: b3ce5bc51b48
Create Date: 2026-10-31 19:45:00.000000

REASON: producto_variantes table exists but is missing the is_active column
that was defined in the original migration (b4bb14c68858) which was never
applied. This migration safely adds the missing column to the existing table.

CONSTRAINTS:
- No data loss
- No table recreation
- Backward compatible (DEFAULT TRUE)
- Safe to apply on running system
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_producto_variantes_is_active'
down_revision: Union[str, Sequence[str], None] = 'b3ce5bc51b48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active column to producto_variantes."""
    op.add_column(
        'producto_variantes',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )


def downgrade() -> None:
    """Remove is_active column from producto_variantes."""
    op.drop_column('producto_variantes', 'is_active')
