"""add brands table (Phase 2 Commerce Core: catalog brands)"""
from alembic import op
import sqlalchemy as sa

revision = '9b2e5f7a3c14'
down_revision = '7f3a1c9d4b21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'brands',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=1024), nullable=True),
        sa.Column('website', sa.String(length=1024), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('seo_title', sa.String(length=255), nullable=True),
        sa.Column('seo_description', sa.String(length=500), nullable=True),
        sa.Column('seo_keywords', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_brand_organization_slug'),
    )


def downgrade() -> None:
    op.drop_table('brands')
