"""add_superadmin_to_rol_usuario_enum_local

Revision ID: 51a31e1a23f9
Revises: d2b8e5f19a4c
Create Date: 2026-10-25 02:28:48.328114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51a31e1a23f9'
down_revision: Union[str, Sequence[str], None] = 'd2b8e5f19a4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add SUPERADMIN to rol_usuario enum."""
    # Add SUPERADMIN to the enum type, placing it BEFORE ADMINISTRADOR
    op.execute("ALTER TYPE rol_usuario ADD VALUE 'SUPERADMIN' BEFORE 'ADMINISTRADOR'")


def downgrade() -> None:
    """Downgrade schema - cannot remove values from enums in PostgreSQL."""
    # Enums in PostgreSQL cannot have values removed without recreating the type,
    # which would require recreating all columns using the enum. SUPERADMIN
    # remains in the enum type after downgrade.
    pass
