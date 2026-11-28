from alembic import context
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from app.config import data_root_from_env
from app.schema.migrate import include_name, target_metadata


def database_url() -> str:
    url = context.config.get_main_option("sqlalchemy.url")
    return url or f"sqlite:///{data_root_from_env() / 'app.db'}"


def configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def set_pragmas(dbapi_connection, _record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def run_migrations() -> None:
    engine = create_engine(database_url())
    configure_sqlite(engine)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


run_migrations()
