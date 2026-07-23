"""add payment_attempts and invoices tables (Phase 4 Orders: payment_attempts, invoices)"""
from alembic import op
import sqlalchemy as sa

revision = 'e2a5c8f1b937'
down_revision = 'd9f3b6e2c714'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'payment_attempts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('order_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('method', sa.String(length=32), nullable=False),
        sa.Column('gateway', sa.String(length=64), nullable=False, server_default='manual'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('gateway_reference', sa.String(length=255), nullable=True),
        sa.Column('gateway_response', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'idempotency_key', name='uq_payment_attempt_organization_idempotency_key'),
    )

    op.create_table(
        'invoices',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('order_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('invoice_number', sa.String(length=50), nullable=False, index=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='issued'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('subtotal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('shipping_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total', sa.Float(), nullable=False, server_default='0'),
        sa.Column('amount_paid', sa.Float(), nullable=False, server_default='0'),
        sa.Column('amount_due', sa.Float(), nullable=False, server_default='0'),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('voided_at', sa.DateTime(), nullable=True),
        sa.Column('void_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'invoice_number', name='uq_invoice_organization_number'),
        sa.UniqueConstraint('organization_id', 'order_id', name='uq_invoice_organization_order'),
    )


def downgrade() -> None:
    op.drop_table('invoices')
    op.drop_table('payment_attempts')
