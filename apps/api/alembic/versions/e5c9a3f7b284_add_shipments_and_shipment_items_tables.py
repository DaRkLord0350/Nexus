"""add shipments and shipment_items tables (Phase 5 Shipping: shipments, shipment_items)"""
from alembic import op
import sqlalchemy as sa

revision = 'e5c9a3f7b284'
down_revision = 'd8b4f2a916c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipments',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipment_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('order_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipping_provider_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('tracking_number', sa.String(length=128), nullable=True, index=True),
        sa.Column('carrier_name', sa.String(length=128), nullable=True),
        sa.Column('service_type', sa.String(length=64), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('shipping_cost', sa.Float(), nullable=False, server_default='0'),
        sa.Column('insurance_amount', sa.Float(), nullable=True),
        sa.Column('is_cod', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('cod_amount', sa.Float(), nullable=True),
        sa.Column('expected_delivery_date', sa.DateTime(), nullable=True),
        sa.Column('picked_up_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['shipping_provider_id'], ['shipping_providers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'shipment_number', name='uq_shipment_organization_number'),
    )

    op.create_table(
        'shipment_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipment_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('order_item_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('product_name', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id']),
    )


def downgrade() -> None:
    op.drop_table('shipment_items')
    op.drop_table('shipments')
