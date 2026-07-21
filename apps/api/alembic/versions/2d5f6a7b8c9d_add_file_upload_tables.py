"""add file upload tables
"""
from alembic import op
import sqlalchemy as sa

revision = '2d5f6a7b8c9d'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'folders',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent_folder_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('path', sa.String(length=1024), nullable=False, index=True),
        sa.UniqueConstraint('organization_id', 'parent_folder_id', 'name', name='uq_folder_parent_name'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_folder_id'], ['folders.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'files',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('folder_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('object_key', sa.String(length=1024), nullable=False, unique=True, index=True),
        sa.Column('storage_provider', sa.String(length=50), nullable=False),
        sa.Column('bucket', sa.String(length=255), nullable=True),
        sa.Column('content_type', sa.String(length=255), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('file_metadata', sa.JSON(), nullable=True),
        sa.Column('uploaded_by', sa.String(length=36), nullable=False, index=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('files')
    op.drop_table('folders')
