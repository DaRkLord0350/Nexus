"""add shipping_rules table (Phase 5 Shipping: shipping_rules)"""
from alembic import op
import sqlalchemy as sa

revision = 'd4a8f2c6e195'
down_revision = 'c2f8b5a917d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipping_rules',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('condition_type', sa.String(length=32), nullable=False),
        sa.Column('condition_value', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=32), nullable=False),
        sa.Column('action_value', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('shipping_rules')
