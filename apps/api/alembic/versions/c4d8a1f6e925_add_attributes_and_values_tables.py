"""add attributes and attribute_values tables (Phase 2 Commerce Core)"""
from alembic import op
import sqlalchemy as sa

revision = 'c4d8a1f6e925'
down_revision = '9b2e5f7a3c14'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'attributes',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=False, index=True),
        sa.Column('input_type', sa.String(length=32), nullable=False, server_default='select'),
        sa.Column('is_variant_attribute', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_attribute_organization_code'),
    )

    op.create_table(
        'attribute_values',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('attribute_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, index=True),
        sa.Column('color_hex', sa.String(length=16), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['attributes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('attribute_id', 'slug', name='uq_attribute_value_attribute_slug'),
    )


def downgrade() -> None:
    op.drop_table('attribute_values')
    op.drop_table('attributes')
