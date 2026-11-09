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
    """Add is_active column to producto_variantes if it doesn't exist."""
    # Check if column already exists
    context = op.get_context()
    inspector = sa.inspect(context.bind)

    columns = {col['name'] for col in inspector.get_columns('producto_variantes')}

    if 'is_active' not in columns:
        # Column doesn't exist - add it
        op.add_column(
            'producto_variantes',
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
        )
    else:
        # Column exists - verify it has correct attributes
        col_info = next(
            (col for col in inspector.get_columns('producto_variantes')
             if col['name'] == 'is_active'),
            None
        )
        if col_info:
            # Verify type is Boolean and nullable is False
            if col_info['type'].__class__.__name__ != 'BOOLEAN' or col_info['nullable']:
                raise Exception(
                    f"Column 'is_active' exists but has unexpected schema: {col_info}. "
                    "Manual intervention required."
                )


def downgrade() -> None:
    """Remove is_active column from producto_variantes."""
    context = op.get_context()
    inspector = sa.inspect(context.bind)

    columns = {col['name'] for col in inspector.get_columns('producto_variantes')}

    if 'is_active' in columns:
        op.drop_column('producto_variantes', 'is_active')
