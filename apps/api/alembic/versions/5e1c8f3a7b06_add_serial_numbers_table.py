"""add serial_numbers table (Phase 3 Inventory: serial_numbers) and inventory_transactions.serial_number_id"""
from alembic import op
import sqlalchemy as sa

revision = '5e1c8f3a7b06'
down_revision = '4d9b2e6c1a73'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'serial_numbers',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('inventory_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('batch_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('bin_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('serial', sa.String(length=150), nullable=False, index=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='available'),
        sa.Column('sold_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['bin_id'], ['warehouse_bins.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('organization_id', 'product_id', 'serial', name='uq_serial_organization_product_serial'),
    )

    with op.batch_alter_table('inventory_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('serial_number_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_inventory_transactions_serial_number_id', ['serial_number_id'])
        batch_op.create_foreign_key(
            'fk_inventory_transactions_serial_number_id_serial_numbers', 'serial_numbers', ['serial_number_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('inventory_transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_inventory_transactions_serial_number_id_serial_numbers', type_='foreignkey')
        batch_op.drop_index('ix_inventory_transactions_serial_number_id')
        batch_op.drop_column('serial_number_id')

    op.drop_table('serial_numbers')
