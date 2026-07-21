"""backfill missing organization_id FKs and indexes

Found during an AWS-migration database audit: organization_id FK constraints
were added consistently for tables created from 2d5f6a7b8c9d onward, but six
tables from the first two migrations never got one (TenantMixin declared the
column without a ForeignKey() at the ORM level, so nothing forced this to be
consistent). Also backfills two columns that were declared index=True in
their model but never actually got an index in their migration.
"""
from alembic import op
import sqlalchemy as sa

revision = 'e9cc59d3fe24'
down_revision = '663dfb1ccdad'
branch_labels = None
depends_on = None


TABLES_MISSING_ORG_FK = [
    'sessions',
    'refresh_tokens',
    'email_verification_tokens',
    'password_reset_tokens',
    'role_permissions',
    'user_roles',
]


def upgrade() -> None:
    for table_name in TABLES_MISSING_ORG_FK:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.create_foreign_key(
                f'fk_{table_name}_organization_id_organizations',
                'organizations',
                ['organization_id'],
                ['id'],
                ondelete='CASCADE',
            )

    op.create_index('ix_email_verification_tokens_user_id', 'email_verification_tokens', ['user_id'])
    op.create_index('ix_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('ix_folders_created_by', 'folders', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_folders_created_by', table_name='folders')
    op.drop_index('ix_password_reset_tokens_user_id', table_name='password_reset_tokens')
    op.drop_index('ix_email_verification_tokens_user_id', table_name='email_verification_tokens')

    for table_name in reversed(TABLES_MISSING_ORG_FK):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.drop_constraint(f'fk_{table_name}_organization_id_organizations', type_='foreignkey')
