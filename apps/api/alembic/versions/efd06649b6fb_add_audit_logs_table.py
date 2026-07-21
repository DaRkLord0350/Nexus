"""add audit logs table
"""
from alembic import op
import sqlalchemy as sa

revision = 'efd06649b6fb'
down_revision = '90ba726121aa'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('action', sa.String(length=64), nullable=False, index=True),
        sa.Column('module', sa.String(length=64), nullable=False, index=True),
        sa.Column('entity', sa.String(length=128), nullable=True, index=True),
        sa.Column('entity_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('request_id', sa.String(length=64), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
