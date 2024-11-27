"""stock_daily date primary key삭제

Revision ID: 38aa17355450
Revises: 69b38d7ca9f4
Create Date: 2024-11-27 22:12:38.504063

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "38aa17355450"
down_revision: Union[str, None] = "69b38d7ca9f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", sa.text("date DESC")], unique=False)
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", sa.text("datetime DESC")], unique=False)
    op.drop_index("idx_code_date", table_name="stock_daily")
    op.create_index("idx_code_date", "stock_daily", ["code", sa.text("date DESC")], unique=False)
    op.drop_index("idx_code_datetime_desc", table_name="stock_minutely")
    op.create_index("idx_code_datetime_desc", "stock_minutely", ["code", sa.text("datetime DESC")], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("idx_code_datetime_desc", table_name="stock_minutely")
    op.create_index("idx_code_datetime_desc", "stock_minutely", ["code", "datetime"], unique=False)
    op.drop_index("idx_code_date", table_name="stock_daily")
    op.create_index("idx_code_date", "stock_daily", ["code", "date"], unique=False)
    op.drop_index("idx_name_datetime", table_name="market_index_minutely")
    op.create_index("idx_name_datetime", "market_index_minutely", ["name", "datetime"], unique=False)
    op.drop_index("idx_name_date_desc", table_name="market_index_daily")
    op.create_index("idx_name_date_desc", "market_index_daily", ["name", "date"], unique=False)
    # ### end Alembic commands ###
