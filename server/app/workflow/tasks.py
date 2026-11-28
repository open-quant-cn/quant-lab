from typing import cast

from huey import SqliteHuey
from huey.storage import SqliteStorage

from app.config import data_root_from_env

# Built at import time because @huey.task() needs the instance. Only reads the
# environment; create_tables=False keeps construction away from the database.
huey = SqliteHuey(
    filename=str(data_root_from_env() / "app.db"),
    utc=False,
    results=False,
    create_tables=False,
)


def initialize_queue_schema() -> None:
    """Create Huey's tables in app.db; serve calls this before starting the consumer."""
    cast(SqliteStorage, huey.storage).initialize_schema()
