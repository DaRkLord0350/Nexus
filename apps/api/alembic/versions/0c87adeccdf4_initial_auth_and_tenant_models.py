"""initial auth and tenant models
"""
from alembic import op
import sqlalchemy as sa


revision = '0c87adeccdf4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    organization_status = sa.Enum(
        "active",
        "suspended",
        "deleted",
        name="organizationstatus",
        native_enum=False,
    )

    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("logo", sa.String(length=1024), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("currency", sa.String(length=16), nullable=True),
        sa.Column("subscription", sa.String(length=64), nullable=True),
        sa.Column("status", organization_status, nullable=False, server_default="active"),
        sa.Column("settings", sa.Text(), nullable=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("first_name", sa.String(length=128), nullable=False),
        sa.Column("last_name", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("profile_picture", sa.String(length=1024), nullable=True),
        sa.Column("profile_metadata", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("device_type", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("last_active_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("session_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("organization_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("password_reset_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("sessions")
    op.drop_table("users")
    op.drop_table("organizations")
