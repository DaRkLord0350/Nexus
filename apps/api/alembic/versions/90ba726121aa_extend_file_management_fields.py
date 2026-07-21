"""extend file management fields
"""
from alembic import op
import sqlalchemy as sa

revision = '90ba726121aa'
down_revision = '2d5f6a7b8c9d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('files', sa.Column('original_filename', sa.String(length=255), nullable=True))
    op.add_column('files', sa.Column('extension', sa.String(length=32), nullable=True))
    op.add_column('files', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.add_column('files', sa.Column('visibility', sa.String(length=20), nullable=False, server_default='private'))
    op.execute("UPDATE files SET original_filename = name WHERE original_filename IS NULL")
    op.create_index('ix_files_checksum', 'files', ['checksum'])

    op.add_column('folders', sa.Column('created_by', sa.String(length=36), nullable=True))
    with op.batch_alter_table('folders') as batch_op:
        batch_op.create_foreign_key('fk_folders_created_by_users', 'users', ['created_by'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('folders') as batch_op:
        batch_op.drop_constraint('fk_folders_created_by_users', type_='foreignkey')
    op.drop_column('folders', 'created_by')

    op.drop_index('ix_files_checksum', table_name='files')
    op.drop_column('files', 'visibility')
    op.drop_column('files', 'checksum')
    op.drop_column('files', 'extension')
    op.drop_column('files', 'original_filename')
