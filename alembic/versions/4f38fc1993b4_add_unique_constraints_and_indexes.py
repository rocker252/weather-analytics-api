"""add unique constraints and indexes

Revision ID: 4f38fc1993b4
Revises: 38dad16e1eba
Create Date: 2025-08-20 12:03:27.285059
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4f38fc1993b4'
down_revision: Union[str, Sequence[str], None] = '38dad16e1eba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraints safely in SQLite
    with op.batch_alter_table("weather") as batch_op:
        batch_op.create_unique_constraint("uix_station_date", ["station_id", "date"])

    with op.batch_alter_table("weather_stats") as batch_op:
        batch_op.alter_column("station_id", existing_type=sa.VARCHAR(), nullable=True)
        batch_op.alter_column("year", existing_type=sa.INTEGER(), nullable=True)
        batch_op.create_unique_constraint("uix_station_year", ["station_id", "year"])
        batch_op.drop_column("recorded_at")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("weather_stats") as batch_op:
        batch_op.add_column(sa.Column("recorded_at", sa.DATETIME(), nullable=True))
        batch_op.drop_constraint("uix_station_year", type_="unique")
        batch_op.alter_column("year", existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column("station_id", existing_type=sa.VARCHAR(), nullable=False)

    with op.batch_alter_table("weather") as batch_op:
        batch_op.drop_constraint("uix_station_date", type_="unique")
