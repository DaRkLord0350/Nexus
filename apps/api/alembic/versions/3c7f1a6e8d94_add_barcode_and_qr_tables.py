"""add barcode and qr code tables (Phase 3 Inventory: barcodes, qr_codes)"""
from alembic import op
import sqlalchemy as sa

revision = '3c7f1a6e8d94'
down_revision = '2b8e5d9a4f61'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'barcodes',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('value', sa.String(length=128), nullable=False, index=True),
        sa.Column('format', sa.String(length=32), nullable=False, server_default='code128'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'format', 'value', name='uq_barcode_organization_format_value'),
    )

    op.create_table(
        'qr_codes',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=32), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('image_url', sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'entity_type', 'entity_id', name='uq_qr_code_organization_entity'),
    )


def downgrade() -> None:
    op.drop_table('qr_codes')
    op.drop_table('barcodes')
