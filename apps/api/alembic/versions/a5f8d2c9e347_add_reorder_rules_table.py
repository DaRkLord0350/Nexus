"""add reorder_rules table (Phase 3 Inventory: reorder_rules)"""
from alembic import op
import sqlalchemy as sa

revision = 'a5f8d2c9e347'
down_revision = '9c6e3a8b5d20'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'reorder_rules',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('minimum_stock', sa.Integer(), nullable=False),
        sa.Column('maximum_stock', sa.Integer(), nullable=True),
        sa.Column('reorder_quantity', sa.Integer(), nullable=False),
        sa.Column('supplier_name', sa.String(length=255), nullable=True),
        sa.Column('lead_time_days', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('reorder_rules')
