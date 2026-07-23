"""add shipment_tracking_events table (Phase 5 Shipping: shipment_tracking_events)"""
from alembic import op
import sqlalchemy as sa

revision = 'a9d2e6f4b837'
down_revision = 'f3a7c1e9d652'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipment_tracking_events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipment_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=32), nullable=False, server_default='manual'),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('shipment_tracking_events')
