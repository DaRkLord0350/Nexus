"""add return_requests and return_items tables (Phase 4 Orders: return_requests, return_items)"""
from alembic import op
import sqlalchemy as sa

revision = 'f6c3d9a2e158'
down_revision = 'e2a5c8f1b937'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'return_requests',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('return_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('order_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('customer_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='requested'),
        sa.Column('resolution', sa.String(length=20), nullable=True),
        sa.Column('reason_code', sa.String(length=64), nullable=False),
        sa.Column('reason_notes', sa.Text(), nullable=True),
        sa.Column('inspection_notes', sa.Text(), nullable=True),
        sa.Column('inspected_by', sa.String(length=36), nullable=True, index=True),
        sa.Column('inspected_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True, index=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id']),
        sa.ForeignKeyConstraint(['inspected_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'return_number', name='uq_return_request_organization_number'),
    )

    op.create_table(
        'return_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('return_request_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('order_item_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reason_code', sa.String(length=64), nullable=True),
        sa.Column('condition', sa.String(length=20), nullable=True),
        sa.Column('image_urls', sa.Text(), nullable=True),
        sa.Column('restocked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('restocked_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['return_request_id'], ['return_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id']),
    )


def downgrade() -> None:
    op.drop_table('return_items')
    op.drop_table('return_requests')
