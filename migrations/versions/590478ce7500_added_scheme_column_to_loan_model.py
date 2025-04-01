"""Added scheme column to loan model

Revision ID: 590478ce7500
Revises: 
Create Date: 2025-03-11 12:32:01.598367

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '590478ce7500'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('_alembic_tmp_loan')
    with op.batch_alter_table('loan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('scheme', sa.String(), nullable=False))
        batch_op.drop_column('id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('loan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.INTEGER(), nullable=False))
        batch_op.drop_column('scheme')

    op.create_table('_alembic_tmp_loan',
    sa.Column('loanId', sa.VARCHAR(length=50), nullable=False),
    sa.Column('bank', sa.VARCHAR(length=100), nullable=False),
    sa.Column('interestRate', sa.FLOAT(), nullable=False),
    sa.Column('maxLoanAmount', sa.FLOAT(), nullable=False),
    sa.Column('tenure', sa.VARCHAR(length=50), nullable=False),
    sa.Column('monthlyEMI', sa.FLOAT(), nullable=False),
    sa.Column('processingFee', sa.FLOAT(), nullable=False),
    sa.Column('prepaymentPenalty', sa.VARCHAR(length=50), nullable=False),
    sa.Column('scheme', sa.VARCHAR(), nullable=False),
    sa.UniqueConstraint('loanId')
    )
    # ### end Alembic commands ###
