"""add pickups table and shipments.pickup_id (Phase 5 Shipping: pickups)"""
from alembic import op
import sqlalchemy as sa

revision = 'c2f8b5a917d4'
down_revision = 'b7e4d1a293f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pickups',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('pickup_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipping_provider_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='scheduled'),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False),
        sa.Column('time_slot', sa.String(length=64), nullable=True),
        sa.Column('contact_name', sa.String(length=128), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['shipping_provider_id'], ['shipping_providers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'pickup_number', name='uq_pickup_organization_number'),
    )

    with op.batch_alter_table('shipments') as batch_op:
        batch_op.add_column(sa.Column('pickup_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_shipments_pickup_id', ['pickup_id'])
        batch_op.create_foreign_key('fk_shipments_pickup_id', 'pickups', ['pickup_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('shipments') as batch_op:
        batch_op.drop_constraint('fk_shipments_pickup_id', type_='foreignkey')
        batch_op.drop_index('ix_shipments_pickup_id')
        batch_op.drop_column('pickup_id')

    op.drop_table('pickups')
