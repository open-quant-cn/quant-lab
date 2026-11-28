import sqlite3
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from huey import SqliteHuey
from sqlalchemy import create_engine

from app.schema.migrate import include_name, target_metadata, upgrade_to_head


def query(db: Path, sql: str) -> list[tuple[object, ...]]:
    with sqlite3.connect(db) as conn:
        return conn.execute(sql).fetchall()


def test_upgrade_creates_versioned_wal_database(tmp_path: Path) -> None:
    db = tmp_path / "app.db"
    upgrade_to_head(db)
    assert query(db, "select version_num from alembic_version") == [("0001",)]
    assert query(db, "pragma journal_mode") == [("wal",)]


def test_upgrade_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "app.db"
    upgrade_to_head(db)
    upgrade_to_head(db)
    assert query(db, "select version_num from alembic_version") == [("0001",)]


def test_autogenerate_leaves_huey_tables_alone(tmp_path: Path) -> None:
    db = tmp_path / "app.db"
    upgrade_to_head(db)
    SqliteHuey(filename=str(db), results=False)
    engine = create_engine(f"sqlite:///{db}")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(
            conn, opts={"include_name": include_name, "target_metadata": target_metadata}
        )
        assert compare_metadata(ctx, target_metadata) == []
    engine.dispose()
