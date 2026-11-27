"""job_search_requests

Revision ID: v4
Revises: v3
Create Date: 2026-11-27 00:00:00.000000

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "v4"
down_revision: Union[str, Sequence[str], None] = "v3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

HERE = Path(__file__).resolve().parent


def upgrade() -> None:
    op.get_bind().exec_driver_sql((HERE / "upgrade.sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    op.get_bind().exec_driver_sql((HERE / "downgrade.sql").read_text(encoding="utf-8"))
