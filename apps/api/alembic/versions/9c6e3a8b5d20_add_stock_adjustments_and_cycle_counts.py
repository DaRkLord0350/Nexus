"""add stock adjustments and cycle counts tables (Phase 3 Inventory: stock_adjustments, cycle_counts, cycle_count_items)"""
from alembic import op
import sqlalchemy as sa

revision = '9c6e3a8b5d20'
down_revision = '8b5d2f7a4c19'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'stock_adjustments',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('adjustment_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('inventory_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('bin_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity_delta', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bin_id'], ['warehouse_bins.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'adjustment_number', name='uq_stock_adjustment_organization_number'),
    )

    op.create_table(
        'cycle_counts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('count_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('zone_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='scheduled'),
        sa.Column('scheduled_date', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to', sa.String(length=36), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['warehouse_zones.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'count_number', name='uq_cycle_count_organization_number'),
    )

    op.create_table(
        'cycle_count_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('cycle_count_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('inventory_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('bin_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('expected_quantity', sa.Integer(), nullable=False),
        sa.Column('actual_quantity', sa.Integer(), nullable=True),
        sa.Column('variance', sa.Integer(), nullable=True),
        sa.Column('counted_at', sa.DateTime(), nullable=True),
        sa.Column('counted_by', sa.String(length=36), nullable=True, index=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cycle_count_id'], ['cycle_counts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bin_id'], ['warehouse_bins.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['counted_by'], ['users.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('cycle_count_items')
    op.drop_table('cycle_counts')
    op.drop_table('stock_adjustments')
