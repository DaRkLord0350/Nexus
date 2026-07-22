"""add products table (Phase 2 Commerce Core: catalog products)"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e7b2a9f341'
down_revision = 'c4d8a1f6e925'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'products',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, index=True),
        sa.Column('sku', sa.String(length=100), nullable=False, index=True),
        sa.Column('barcode', sa.String(length=100), nullable=True, index=True),
        sa.Column('brand_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('category_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('short_description', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('seo_title', sa.String(length=255), nullable=True),
        sa.Column('seo_description', sa.String(length=500), nullable=True),
        sa.Column('seo_keywords', sa.String(length=500), nullable=True),
        sa.Column('length', sa.Float(), nullable=True),
        sa.Column('width', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('dimension_unit', sa.String(length=16), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('weight_unit', sa.String(length=16), nullable=True),
        sa.Column('origin_country', sa.String(length=128), nullable=True),
        sa.Column('vendor', sa.String(length=255), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('search_keywords', sa.Text(), nullable=True),
        sa.Column('track_inventory', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('allow_backorders', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('has_variants', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_product_organization_slug'),
        sa.UniqueConstraint('organization_id', 'sku', name='uq_product_organization_sku'),
    )
    op.create_index('ix_products_status', 'products', ['status'])


def downgrade() -> None:
    op.drop_table('products')
