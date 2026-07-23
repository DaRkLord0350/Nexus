"""add shipping_rates table (Phase 5 Shipping: shipping_rates)"""
from alembic import op
import sqlalchemy as sa

revision = 'f3a7c1e9d652'
down_revision = 'e5c9a3f7b284'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipping_rates',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipping_provider_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('origin_country', sa.String(length=2), nullable=True),
        sa.Column('destination_country', sa.String(length=2), nullable=True, index=True),
        sa.Column('destination_state', sa.String(length=64), nullable=True, index=True),
        sa.Column('min_weight', sa.Float(), nullable=True),
        sa.Column('max_weight', sa.Float(), nullable=True),
        sa.Column('base_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('price_per_kg', sa.Float(), nullable=True),
        sa.Column('cod_fee', sa.Float(), nullable=True),
        sa.Column('insurance_fee', sa.Float(), nullable=True),
        sa.Column('transit_days_min', sa.Integer(), nullable=True),
        sa.Column('transit_days_max', sa.Integer(), nullable=True),
        sa.Column('delivery_rating', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipping_provider_id'], ['shipping_providers.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('shipping_rates')
