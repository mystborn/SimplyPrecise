"""about

Revision ID: ad7578819a15
Revises: cea0d12853da
Create Date: 2019-10-13 17:47:13.098987

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad7578819a15'
down_revision = 'cea0d12853da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('name', sa.String(length=128), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'name')
    # ### end Alembic commands ###
