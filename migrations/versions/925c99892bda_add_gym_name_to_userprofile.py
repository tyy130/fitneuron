"""Add gym_name to UserProfile

Revision ID: 925c99892bda
Revises: 6e902fb31b68
Create Date: 2024-08-18 11:01:19.210623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '925c99892bda'
down_revision = '6e902fb31b68'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_profile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gym_name', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_profile', schema=None) as batch_op:
        batch_op.drop_column('gym_name')

    # ### end Alembic commands ###
