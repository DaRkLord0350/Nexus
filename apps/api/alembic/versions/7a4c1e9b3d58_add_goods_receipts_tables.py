"""add goods receipts tables (Phase 3 Inventory: goods_receipts, goods_receipt_items)"""
from alembic import op
import sqlalchemy as sa

revision = '7a4c1e9b3d58'
down_revision = '6f2a9d4c8e17'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'goods_receipts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('receipt_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('purchase_order_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('receiver_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('received_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'receipt_number', name='uq_goods_receipt_organization_number'),
    )

    op.create_table(
        'goods_receipt_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('goods_receipt_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('purchase_order_item_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity_received', sa.Integer(), nullable=False),
        sa.Column('unit_cost', sa.Float(), nullable=True),
        sa.Column('batch_number', sa.String(length=100), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('manufactured_date', sa.DateTime(), nullable=True),
        sa.Column('bin_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['goods_receipt_id'], ['goods_receipts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_order_item_id'], ['purchase_order_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bin_id'], ['warehouse_bins.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('goods_receipt_items')
    op.drop_table('goods_receipts')
