"""add marketplace tables (Phase 6 Marketplace: marketplace_connectors, marketplace_product_links, marketplace_order_links, marketplace_sync_logs, marketplace_webhook_events)"""
from alembic import op
import sqlalchemy as sa

revision = 'f3b7c9d1a204'
down_revision = 'e7c1a3f9b482'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'marketplace_connectors',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False, index=True),
        sa.Column('connector_type', sa.String(length=32), nullable=False, server_default='other', index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('credentials', sa.Text(), nullable=True),
        sa.Column('webhook_secret', sa.String(length=255), nullable=True),
        sa.Column('store_url', sa.String(length=500), nullable=True),
        sa.Column('auto_sync_products', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('auto_sync_orders', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('auto_sync_inventory', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('auto_sync_prices', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_status', sa.String(length=16), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'code', name='uq_marketplace_connector_organization_code'),
    )

    op.create_table(
        'marketplace_product_links',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('marketplace_connector_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('external_id', sa.String(length=255), nullable=True, index=True),
        sa.Column('external_sku', sa.String(length=100), nullable=True),
        sa.Column('external_url', sa.String(length=500), nullable=True),
        sa.Column('sync_status', sa.String(length=16), nullable=False, server_default='pending', index=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_synced_price', sa.Float(), nullable=True),
        sa.Column('last_synced_quantity', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['marketplace_connector_id'], ['marketplace_connectors.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.UniqueConstraint('marketplace_connector_id', 'product_id', name='uq_marketplace_product_link_connector_product'),
    )

    op.create_table(
        'marketplace_order_links',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('marketplace_connector_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('order_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('external_order_id', sa.String(length=255), nullable=False, index=True),
        sa.Column('external_order_number', sa.String(length=100), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='imported', index=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['marketplace_connector_id'], ['marketplace_connectors.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.UniqueConstraint('marketplace_connector_id', 'external_order_id', name='uq_marketplace_order_link_connector_external_id'),
    )

    op.create_table(
        'marketplace_sync_logs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('marketplace_connector_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('sync_type', sa.String(length=16), nullable=False, index=True),
        sa.Column('status', sa.String(length=16), nullable=False, index=True),
        sa.Column('triggered_by', sa.String(length=16), nullable=False, server_default='manual'),
        sa.Column('items_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('items_succeeded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('items_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['marketplace_connector_id'], ['marketplace_connectors.id']),
    )

    op.create_table(
        'marketplace_webhook_events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('marketplace_connector_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('event_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='pending', index=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['marketplace_connector_id'], ['marketplace_connectors.id']),
    )


def downgrade() -> None:
    op.drop_table('marketplace_webhook_events')
    op.drop_table('marketplace_sync_logs')
    op.drop_table('marketplace_order_links')
    op.drop_table('marketplace_product_links')
    op.drop_table('marketplace_connectors')
