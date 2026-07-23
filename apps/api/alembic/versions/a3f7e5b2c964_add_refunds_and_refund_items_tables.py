"""add refunds and refund_items tables (Phase 4 Orders: refunds, refund_items)"""
from alembic import op
import sqlalchemy as sa

revision = 'a3f7e5b2c964'
down_revision = 'f6c3d9a2e158'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'refunds',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('refund_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('order_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('return_request_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('customer_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('payment_attempt_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('method', sa.String(length=32), nullable=False, server_default='original_payment'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='requested'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('requested_by', sa.String(length=36), nullable=True, index=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True, index=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['return_request_id'], ['return_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['payment_attempt_id'], ['payment_attempts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'refund_number', name='uq_refund_organization_number'),
    )

    op.create_table(
        'refund_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('refund_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('order_item_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['refund_id'], ['refunds.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_item_id'], ['order_items.id']),
    )


def downgrade() -> None:
    op.drop_table('refund_items')
    op.drop_table('refunds')
