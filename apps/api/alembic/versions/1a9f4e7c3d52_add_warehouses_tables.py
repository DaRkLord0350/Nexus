"""add warehouses tables (Phase 3 Inventory: warehouses, warehouse_zones, warehouse_bins)"""
from alembic import op
import sqlalchemy as sa

revision = '1a9f4e7c3d52'
down_revision = 'c7f2a5e9b361'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'warehouses',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, index=True),
        sa.Column('warehouse_type', sa.String(length=32), nullable=False, server_default='main'),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('country', sa.String(length=128), nullable=True),
        sa.Column('state', sa.String(length=128), nullable=True),
        sa.Column('city', sa.String(length=128), nullable=True),
        sa.Column('zipcode', sa.String(length=32), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'code', name='uq_warehouse_organization_code'),
    )

    op.create_table(
        'warehouse_zones',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, index=True),
        sa.Column('zone_type', sa.String(length=32), nullable=False, server_default='storage'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('warehouse_id', 'code', name='uq_warehouse_zone_warehouse_code'),
    )

    op.create_table(
        'warehouse_bins',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('zone_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('code', sa.String(length=50), nullable=False, index=True),
        sa.Column('aisle', sa.String(length=50), nullable=True),
        sa.Column('rack', sa.String(length=50), nullable=True),
        sa.Column('shelf', sa.String(length=50), nullable=True),
        sa.Column('bin_number', sa.String(length=50), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['warehouse_zones.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('warehouse_id', 'code', name='uq_warehouse_bin_warehouse_code'),
    )


def downgrade() -> None:
    op.drop_table('warehouse_bins')
    op.drop_table('warehouse_zones')
    op.drop_table('warehouses')
