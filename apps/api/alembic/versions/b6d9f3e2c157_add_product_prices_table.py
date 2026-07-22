"""add product_prices table (Phase 2 Commerce Core: dedicated pricing model)"""
from alembic import op
import sqlalchemy as sa

revision = 'b6d9f3e2c157'
down_revision = 'a7c2e4f8d013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'product_prices',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('currency', sa.String(length=3), nullable=False, index=True),
        sa.Column('mrp', sa.Float(), nullable=True),
        sa.Column('selling_price', sa.Float(), nullable=False),
        sa.Column('cost_price', sa.Float(), nullable=True),
        sa.Column('compare_price', sa.Float(), nullable=True),
        sa.Column('min_price', sa.Float(), nullable=True),
        sa.Column('max_price', sa.Float(), nullable=True),
        sa.Column('customer_group', sa.String(length=64), nullable=True, index=True),
        sa.Column('region', sa.String(length=64), nullable=True, index=True),
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('effective_to', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('product_prices')
