"""add inventory core tables (Phase 3 Inventory: inventory, inventory_transactions)"""
from alembic import op
import sqlalchemy as sa

revision = '2b8e5d9a4f61'
down_revision = '1a9f4e7c3d52'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'inventory',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('bin_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity_available', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_reserved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_incoming', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_damaged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_returned', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('minimum_stock', sa.Integer(), nullable=True),
        sa.Column('maximum_stock', sa.Integer(), nullable=True),
        sa.Column('reorder_point', sa.Integer(), nullable=True),
        sa.Column('average_cost', sa.Float(), nullable=True),
        sa.Column('last_counted_at', sa.DateTime(), nullable=True),
        sa.Column('low_stock_notified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bin_id'], ['warehouse_bins.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'inventory_transactions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('inventory_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('type', sa.String(length=32), nullable=False, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('quantity_before', sa.Integer(), nullable=True),
        sa.Column('quantity_after', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True, index=True),
        sa.Column('reference_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('user_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('inventory_transactions')
    op.drop_table('inventory')
