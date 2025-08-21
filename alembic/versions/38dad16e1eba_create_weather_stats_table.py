"""create weather_stats table

Revision ID: 38dad16e1eba
Revises: a5d3d10daea1
Create Date: 2025-08-19 14:38:35.089579

"""
from typing import Sequence, Union
from datetime import datetime
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38dad16e1eba'
down_revision: Union[str, Sequence[str], None] = 'a5d3d10daea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'weather_stats',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('station_id', sa.String, index=True, nullable=False),
        sa.Column('year', sa.Integer, index=True, nullable=False),
        sa.Column('avg_max_temp', sa.Float, nullable=True),
        sa.Column('avg_min_temp', sa.Float, nullable=True),
        sa.Column('total_precipitation', sa.Float, nullable=True),
        sa.Column('recorded_at', sa.DateTime, default=datetime.utcnow),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('weather_stats')
