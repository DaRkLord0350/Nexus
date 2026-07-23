"""add wishlists table (Phase 4 Orders: wishlists)"""
from alembic import op
import sqlalchemy as sa

revision = 'c1d4f8a6b273'
down_revision = 'a3f7e5b2c964'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'wishlists',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('customer_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('wishlists')
