from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import settings
from app.models import Base, UTCDateTime

target_metadata = Base.metadata


def render_item(type_, obj, autogen_context):
    # Keep migrations free of app imports: UTCDateTime is plain timestamptz in the database
    if type_ == "type" and isinstance(obj, UTCDateTime):
        autogen_context.imports.add("import sqlalchemy as sa")
        return "sa.DateTime(timezone=True)"
    return False


def run_migrations_offline() -> None:
    context.configure(
        url=settings.migration_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_item=render_item,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Always the direct connection: DDL does not belong behind the PgBouncer pooler
    engine = create_engine(settings.migration_database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
