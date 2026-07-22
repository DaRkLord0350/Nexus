"""add custom_field_definitions and custom_field_values tables (Phase 2.5)"""
from alembic import op
import sqlalchemy as sa

revision = 'c7f2a5e9b361'
down_revision = 'b3e6c9a2d174'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'custom_field_definitions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=32), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False, index=True),
        sa.Column('field_type', sa.String(length=32), nullable=False, server_default='text'),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'entity_type', 'key', name='uq_custom_field_definition_org_entity_key'),
    )

    op.create_table(
        'custom_field_values',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('definition_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('entity_type', sa.String(length=32), nullable=False, index=True),
        sa.Column('entity_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['definition_id'], ['custom_field_definitions.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('definition_id', 'entity_id', name='uq_custom_field_value_definition_entity'),
    )


def downgrade() -> None:
    op.drop_table('custom_field_values')
    op.drop_table('custom_field_definitions')
