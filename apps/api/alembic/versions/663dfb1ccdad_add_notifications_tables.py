"""add notifications tables

This was missing from the original notifications module: the ORM models
(app/models/notification.py, app/models/notification_preference.py) existed
and were exercised by tests via Base.metadata.create_all, but no migration
ever created these tables, so `alembic upgrade head` alone never provisioned
them on a real database.
"""
from alembic import op
import sqlalchemy as sa

revision = '663dfb1ccdad'
down_revision = 'efd06649b6fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('actor_id', sa.String(length=36), nullable=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.Enum('success', 'warning', 'error', 'info', name='notification_type'), nullable=False),
        sa.Column('channel', sa.Enum('in_app', 'email', 'database', 'sms', name='notification_channel'), nullable=False, server_default='in_app'),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('user_id', sa.String(length=36), nullable=False, index=True),
        sa.Column('channel', sa.Enum('in_app', 'email', 'sms', name='notification_preference_channel'), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.UniqueConstraint('organization_id', 'user_id', 'channel', name='uq_notification_preference'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    bind = op.get_bind()
    sa.Enum(name='notification_preference_channel').drop(bind, checkfirst=True)
    sa.Enum(name='notification_channel').drop(bind, checkfirst=True)
    sa.Enum(name='notification_type').drop(bind, checkfirst=True)
