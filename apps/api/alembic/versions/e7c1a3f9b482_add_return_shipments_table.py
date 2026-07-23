"""add return_shipments table (Phase 5 Shipping: return_shipments)"""
from alembic import op
import sqlalchemy as sa

revision = 'e7c1a3f9b482'
down_revision = 'd4a8f2c6e195'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'return_shipments',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('return_shipment_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('return_request_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipping_provider_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('tracking_number', sa.String(length=128), nullable=True, index=True),
        sa.Column('carrier_name', sa.String(length=128), nullable=True),
        sa.Column('pickup_contact_name', sa.String(length=128), nullable=True),
        sa.Column('pickup_contact_phone', sa.String(length=50), nullable=True),
        sa.Column('pickup_line1', sa.String(length=255), nullable=True),
        sa.Column('pickup_city', sa.String(length=128), nullable=True),
        sa.Column('pickup_state', sa.String(length=128), nullable=True),
        sa.Column('pickup_postal_code', sa.String(length=32), nullable=True),
        sa.Column('pickup_country', sa.String(length=2), nullable=True),
        sa.Column('reverse_pickup_scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('reverse_pickup_completed_at', sa.DateTime(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['return_request_id'], ['return_requests.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['shipping_provider_id'], ['shipping_providers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'return_shipment_number', name='uq_return_shipment_organization_number'),
    )


def downgrade() -> None:
    op.drop_table('return_shipments')
