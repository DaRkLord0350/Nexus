"""add SEO fields to categories/brands/products/collections + slug_redirects table (Phase 2.5)"""
from alembic import op
import sqlalchemy as sa

revision = 'a1d4e7f3c852'
down_revision = 'f8a3c1e6b940'
branch_labels = None
depends_on = None

SEO_TABLES = ['categories', 'brands', 'products', 'collections']


def upgrade() -> None:
    for table in SEO_TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column('og_image_url', sa.String(length=1024), nullable=True))
            batch_op.add_column(sa.Column('canonical_url', sa.String(length=1024), nullable=True))
            batch_op.add_column(sa.Column('no_index', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    op.create_table(
        'slug_redirects',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=32), nullable=False, index=True),
        sa.Column('old_slug', sa.String(length=1024), nullable=False, index=True),
        sa.Column('new_slug', sa.String(length=1024), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('slug_redirects')

    for table in SEO_TABLES:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_column('no_index')
            batch_op.drop_column('canonical_url')
            batch_op.drop_column('og_image_url')
