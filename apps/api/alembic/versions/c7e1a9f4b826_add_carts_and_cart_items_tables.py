"""add carts and cart_items tables (Phase 4 Orders: carts, cart_items)"""
from alembic import op
import sqlalchemy as sa

revision = 'c7e1a9f4b826'
down_revision = 'b4d6e9f2a583'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'carts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('customer_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('session_token', sa.String(length=128), nullable=True, index=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('coupon_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('coupon_code', sa.String(length=64), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=False, server_default='0'),
        sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('tax_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('shipping_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total', sa.Float(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('order_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['coupon_id'], ['coupons.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'cart_items',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('cart_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('product_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('variant_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('saved_for_later', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('gift_note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cart_id'], ['carts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('cart_items')
    op.drop_table('carts')
