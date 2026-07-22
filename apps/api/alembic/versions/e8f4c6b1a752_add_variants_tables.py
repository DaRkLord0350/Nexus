"""add variants and variant_attribute_values tables (Phase 2 Commerce Core)"""
from alembic import op
import sqlalchemy as sa

revision = 'e8f4c6b1a752'
down_revision = 'd5e7b2a9f341'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'variants',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('sku', sa.String(length=100), nullable=False, index=True),
        sa.Column('barcode', sa.String(length=100), nullable=True, index=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('weight_unit', sa.String(length=16), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'sku', name='uq_variant_organization_sku'),
    )

    op.create_table(
        'variant_attribute_values',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('attribute_value_id', sa.String(length=36), nullable=False, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_value_id'], ['attribute_values.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('variant_id', 'attribute_value_id', name='uq_variant_attribute_value'),
    )


def downgrade() -> None:
    op.drop_table('variant_attribute_values')
    op.drop_table('variants')
