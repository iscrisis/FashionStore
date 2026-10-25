"""add superadmin to rol_usuario enum

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, Sequence[str], None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add SUPERADMIN to rol_usuario enum."""
    # Add SUPERADMIN to the enum type
    op.execute("ALTER TYPE rol_usuario ADD VALUE 'SUPERADMIN' BEFORE 'ADMINISTRADOR'")


def downgrade() -> None:
    """Downgrade schema - cannot remove values from enums in PostgreSQL."""
    pass
