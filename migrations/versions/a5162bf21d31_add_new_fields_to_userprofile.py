"""Add new fields to UserProfile

Revision ID: a5162bf21d31
Revises: cd3b52e40c17
Create Date: 2024-08-23 11:54:34.512383

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5162bf21d31'
down_revision = 'cd3b52e40c17'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_profile', schema=None) as batch_op:
        batch_op.add_column(sa.Column('use_metric', sa.Boolean(), nullable=True))
        batch_op.alter_column('height',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_profile', schema=None) as batch_op:
        batch_op.alter_column('height',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)
        batch_op.drop_column('use_metric')

    # ### end Alembic commands ###
