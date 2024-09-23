"""empty message

Revision ID: 83b5474b998a
Revises: 1e0dce4a84ed
Create Date: 2024-09-11 13:42:44.748940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '83b5474b998a'
down_revision: Union[str, None] = '1e0dce4a84ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('user_table_email_key', 'user_table', type_='unique')
    op.drop_constraint('user_table_phone_number_key', 'user_table', type_='unique')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('user_table_phone_number_key', 'user_table', ['phone_number'])
    op.create_unique_constraint('user_table_email_key', 'user_table', ['email'])
    # ### end Alembic commands ###
