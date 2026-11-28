from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData

SCRIPT_LOCATION = Path(__file__).resolve().parent

# Huey creates these in app.db with fixed names; autogenerate must never drop them.
HUEY_TABLES = frozenset({"kv", "schedule", "task", "counter"})

target_metadata = MetaData()


def include_name(name: str | None, type_: str, _parent_names: object) -> bool:
    return not (type_ == "table" and name in HUEY_TABLES)


def alembic_config(app_db: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(SCRIPT_LOCATION))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{app_db}")
    return config


def upgrade_to_head(app_db: Path) -> None:
    command.upgrade(alembic_config(app_db), "head")
