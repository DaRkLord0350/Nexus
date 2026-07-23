"""add shipping_providers table (Phase 5 Shipping: shipping_providers)"""
from alembic import op
import sqlalchemy as sa

revision = 'd8b4f2a916c7'
down_revision = 'c1d4f8a6b273'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipping_providers',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False, index=True),
        sa.Column('provider_type', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('credentials', sa.Text(), nullable=True),
        sa.Column('webhook_secret', sa.String(length=255), nullable=True),
        sa.Column('supports_cod', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('supports_insurance', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('supports_reverse_pickup', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('supports_international', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('base_rate', sa.Float(), nullable=True),
        sa.Column('base_transit_days', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'code', name='uq_shipping_provider_organization_code'),
    )


def downgrade() -> None:
    op.drop_table('shipping_providers')
