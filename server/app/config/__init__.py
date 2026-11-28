import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DATA_ROOT_ENV = "QUANT_LAB_DATA_ROOT"
TIMEZONE = "Asia/Shanghai"
CONFIG_FILE = "config.toml"

DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


class ConfigError(Exception):
    pass


def data_root_from_env(env: Mapping[str, str] = os.environ) -> Path:
    raw = env.get(DATA_ROOT_ENV)
    return Path(raw).expanduser().resolve() if raw else DEFAULT_DATA_ROOT


@dataclass(frozen=True)
class Settings:
    data_root: Path
    workers: int

    @property
    def app_db(self) -> Path:
        return self.data_root / "app.db"

    @property
    def consumer_lock(self) -> Path:
        return self.data_root / "consumer.lock"

    @property
    def logs_dir(self) -> Path:
        return self.data_root / "logs"

    def ensure_dirs(self) -> None:
        self.logs_dir.mkdir(exist_ok=True)


def read_config_file(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ConfigError(
            f"missing {path}; copy server/config/config.example.toml there and edit it"
        )
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid TOML in {path}: {exc}") from exc


def parse_workers(raw: Mapping[str, object], path: Path) -> int:
    consumer = raw.get("consumer")
    if not isinstance(consumer, dict) or "workers" not in consumer:
        raise ConfigError(f"{path}: [consumer] workers is required")
    workers = consumer["workers"]
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ConfigError(f"{path}: [consumer] workers must be an integer >= 1, got {workers!r}")
    return workers


def load_settings(env: Mapping[str, str] = os.environ) -> Settings:
    data_root = data_root_from_env(env)
    path = data_root / CONFIG_FILE
    raw = read_config_file(path)
    return Settings(data_root=data_root, workers=parse_workers(raw, path))
