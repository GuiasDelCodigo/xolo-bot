"""job_offers_sync_columns

Revision ID: v3
Revises: v2
Create Date: 2026-11-26 00:00:00.000000

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "v3"
down_revision: Union[str, Sequence[str], None] = "v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HERE = Path(__file__).resolve().parent


def upgrade() -> None:
    op.get_bind().exec_driver_sql((HERE / "upgrade.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.get_bind().exec_driver_sql((HERE / "downgrade.sql").read_text(encoding="utf-8"))
