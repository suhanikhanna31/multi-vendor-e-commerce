"""add ml_model_versions table

Revision ID: 160364ee0504
Revises: 82af0b6f27a1
Create Date: 2026-07-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '160364ee0504'
down_revision = '82af0b6f27a1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ml_model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('vendor_id', sa.Integer(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('feature_columns', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('ml_model_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ml_model_versions_name'), ['name'], unique=False)
        batch_op.create_index(
            batch_op.f('ix_ml_model_versions_created_at'), ['created_at'], unique=False
        )


def downgrade():
    with op.batch_alter_table('ml_model_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ml_model_versions_created_at'))
        batch_op.drop_index(batch_op.f('ix_ml_model_versions_name'))

    op.drop_table('ml_model_versions')
