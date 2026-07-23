"""add shipping_labels table (Phase 5 Shipping: shipping_labels)"""
from alembic import op
import sqlalchemy as sa

revision = 'b7e4d1a293f6'
down_revision = 'a9d2e6f4b837'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipping_labels',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('shipment_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('label_type', sa.String(length=20), nullable=False, server_default='label'),
        sa.Column('format', sa.String(length=16), nullable=False, server_default='html'),
        sa.Column('generated_by', sa.String(length=36), nullable=True, index=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shipment_id'], ['shipments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id']),
    )


def downgrade() -> None:
    op.drop_table('shipping_labels')
