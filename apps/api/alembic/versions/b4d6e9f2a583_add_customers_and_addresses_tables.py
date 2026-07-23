"""add customers and addresses tables (Phase 4 Orders: customers, addresses)"""
from alembic import op
import sqlalchemy as sa

revision = 'b4d6e9f2a583'
down_revision = 'a5f8d2c9e347'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'customers',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('email', sa.String(length=255), nullable=False, index=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=128), nullable=False),
        sa.Column('last_name', sa.String(length=128), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('is_guest', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('accepts_marketing', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=36), nullable=True, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.UniqueConstraint('organization_id', 'email', name='uq_customer_organization_email'),
    )

    op.create_table(
        'addresses',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('customer_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('label', sa.String(length=64), nullable=True),
        sa.Column('address_type', sa.String(length=20), nullable=False, server_default='shipping'),
        sa.Column('first_name', sa.String(length=128), nullable=False),
        sa.Column('last_name', sa.String(length=128), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('line1', sa.String(length=255), nullable=False),
        sa.Column('line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=128), nullable=False),
        sa.Column('state', sa.String(length=128), nullable=True),
        sa.Column('postal_code', sa.String(length=32), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('addresses')
    op.drop_table('customers')
