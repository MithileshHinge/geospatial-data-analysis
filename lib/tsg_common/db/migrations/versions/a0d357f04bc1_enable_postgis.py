"""enable postgis

Revision ID: a0d357f04bc1
Revises:
Create Date: 2025-05-06 09:03:37.029005

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a0d357f04bc1"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS postgis")
