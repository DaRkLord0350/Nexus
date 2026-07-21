"""rbac and organization invitations
"""
from alembic import op
import sqlalchemy as sa

revision = '1a2b3c4d5e6f'
down_revision = '0c87adeccdf4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('code', sa.String(length=64), nullable=False, index=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.UniqueConstraint('organization_id', 'code', name='uq_organization_permission_code'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=128), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('built_in', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.UniqueConstraint('organization_id', 'name', name='uq_organization_role_name'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'role_permissions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('role_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('permission_id', sa.String(length=36), nullable=False, index=True),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'user_roles',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('role_id', sa.String(length=36), nullable=False, index=True),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'organization_invitations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('email', sa.String(length=255), nullable=False, index=True),
        sa.Column('invited_by_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('organization_invitations')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')
