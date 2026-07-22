"""add batches table (Phase 3 Inventory: batches) and inventory_transactions.batch_id"""
from alembic import op
import sqlalchemy as sa

revision = '4d9b2e6c1a73'
down_revision = '3c7f1a6e8d94'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'batches',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('inventory_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('warehouse_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('batch_number', sa.String(length=100), nullable=False, index=True),
        sa.Column('manufactured_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True, index=True),
        sa.Column('received_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('remaining_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('cost_price', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inventory_id'], ['inventory.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('organization_id', 'product_id', 'warehouse_id', 'batch_number', name='uq_batch_organization_product_warehouse_number'),
    )

    with op.batch_alter_table('inventory_transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('batch_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_inventory_transactions_batch_id', ['batch_id'])
        batch_op.create_foreign_key(
            'fk_inventory_transactions_batch_id_batches', 'batches', ['batch_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('inventory_transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_inventory_transactions_batch_id_batches', type_='foreignkey')
        batch_op.drop_index('ix_inventory_transactions_batch_id')
        batch_op.drop_column('batch_id')

    op.drop_table('batches')
