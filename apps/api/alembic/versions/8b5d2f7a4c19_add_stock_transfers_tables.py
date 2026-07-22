"""add stock transfers tables (Phase 3 Inventory: stock_transfers, stock_transfer_items)"""
from alembic import op
import sqlalchemy as sa

revision = '8b5d2f7a4c19'
down_revision = '7a4c1e9b3d58'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'stock_transfers',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('transfer_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('from_warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('to_warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('shipped_at', sa.DateTime(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'transfer_number', name='uq_stock_transfer_organization_number'),
    )

    op.create_table(
        'stock_transfer_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('stock_transfer_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity_requested', sa.Integer(), nullable=False),
        sa.Column('quantity_shipped', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('batch_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_transfer_id'], ['stock_transfers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('stock_transfer_items')
    op.drop_table('stock_transfers')
