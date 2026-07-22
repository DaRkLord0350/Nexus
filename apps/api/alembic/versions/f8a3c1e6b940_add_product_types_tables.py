"""add product_types and product_type_attributes tables; link products.product_type_id (Phase 2.5)"""
from alembic import op
import sqlalchemy as sa

revision = 'f8a3c1e6b940'
down_revision = 'e4b7c2a9f316'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'product_types',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_product_type_organization_slug'),
    )

    op.create_table(
        'product_type_attributes',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_type_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('attribute_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_type_id'], ['product_types.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['attributes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('product_type_id', 'attribute_id', name='uq_product_type_attribute'),
    )

    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('product_type_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_products_product_type_id', ['product_type_id'])
        batch_op.create_foreign_key('fk_products_product_type_id', 'product_types', ['product_type_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint('fk_products_product_type_id', type_='foreignkey')
        batch_op.drop_index('ix_products_product_type_id')
        batch_op.drop_column('product_type_id')

    op.drop_table('product_type_attributes')
    op.drop_table('product_types')
