"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-20 13:40:32.305560

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("users", "google_accounts", "objectives", "sessions")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "google_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("google_sub", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_google_accounts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_google_accounts")),
        sa.UniqueConstraint("google_sub", name=op.f("uq_google_accounts_google_sub")),
        sa.UniqueConstraint("user_id", name=op.f("uq_google_accounts_user_id")),
    )
    op.create_table(
        "objectives",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), server_default="", nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column(
            "mode",
            sa.Enum("daily", "weekly", "monthly", name="mode", native_enum=False, length=16),
            nullable=False,
        ),
        sa.Column("archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=True),
        sa.Column("event_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "mode IN ('daily', 'weekly', 'monthly')", name=op.f("ck_objectives_mode_valid")
        ),
        sa.CheckConstraint(
            "(event_id IS NULL) = (event_start IS NULL) AND (event_id IS NULL) = (event_end IS NULL)",
            name=op.f("ck_objectives_event_all_or_none"),
        ),
        sa.CheckConstraint("minutes BETWEEN 5 AND 1440", name=op.f("ck_objectives_minutes_range")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_objectives_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_objectives")),
    )
    op.create_index(
        "ix_objectives_user_id_created_at", "objectives", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")),
    )
    op.create_index(op.f("ix_sessions_expires_at"), "sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"], unique=False)

    # The ORM bumps updated_at on its own writes; the trigger covers edits made outside the app
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION set_updated_at() RETURNS trigger AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
        for table in TABLES:
            op.execute(
                f"CREATE TRIGGER trg_{table}_updated_at BEFORE UPDATE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
            )


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "postgresql":
        for table in TABLES:
            op.execute(f"DROP TRIGGER trg_{table}_updated_at ON {table}")
        op.execute("DROP FUNCTION set_updated_at()")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_objectives_user_id_created_at", table_name="objectives")
    op.drop_table("objectives")
    op.drop_table("google_accounts")
    op.drop_table("users")
