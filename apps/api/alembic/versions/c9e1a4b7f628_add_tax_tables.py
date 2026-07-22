"""add tax_classes and tax_rates tables; link products.tax_class_id (Phase 2 Commerce Core)"""
from alembic import op
import sqlalchemy as sa

revision = 'c9e1a4b7f628'
down_revision = 'b6d9f3e2c157'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'tax_classes',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_tax_class_organization_code'),
    )

    op.create_table(
        'tax_rates',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('tax_class_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('country', sa.String(length=2), nullable=False, index=True),
        sa.Column('state', sa.String(length=64), nullable=True, index=True),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('tax_type', sa.String(length=32), nullable=False, server_default='other'),
        sa.Column('is_inclusive', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tax_class_id'], ['tax_classes.id'], ondelete='CASCADE'),
    )

    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('tax_class_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_products_tax_class_id', ['tax_class_id'])
        batch_op.create_foreign_key('fk_products_tax_class_id', 'tax_classes', ['tax_class_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_constraint('fk_products_tax_class_id', type_='foreignkey')
        batch_op.drop_index('ix_products_tax_class_id')
        batch_op.drop_column('tax_class_id')

    op.drop_table('tax_rates')
    op.drop_table('tax_classes')
