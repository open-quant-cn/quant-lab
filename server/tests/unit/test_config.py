from pathlib import Path

import pytest

from app.config import (
    DATA_ROOT_ENV,
    DEFAULT_DATA_ROOT,
    ConfigError,
    Settings,
    data_root_from_env,
    load_settings,
)

EXAMPLE = Path(__file__).resolve().parents[2] / "config" / "config.example.toml"


def write_config(root: Path, body: str) -> None:
    (root / "config.toml").write_text(body)


def test_data_root_defaults_to_repo_data_dir() -> None:
    assert data_root_from_env({}) == DEFAULT_DATA_ROOT
    assert (DEFAULT_DATA_ROOT / ".keep").exists()


def test_settings_come_from_data_root_config(tmp_path: Path) -> None:
    write_config(tmp_path, "[consumer]\nworkers = 3\n")
    settings = load_settings({DATA_ROOT_ENV: str(tmp_path)})
    assert settings.data_root == tmp_path.resolve()
    assert settings.workers == 3
    assert settings.app_db == tmp_path.resolve() / "app.db"
    assert settings.consumer_lock == tmp_path.resolve() / "consumer.lock"


def test_example_config_is_loadable(tmp_path: Path) -> None:
    write_config(tmp_path, EXAMPLE.read_text())
    assert load_settings({DATA_ROOT_ENV: str(tmp_path)}).workers == 2


def test_missing_config_file_fails(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="missing .*config.toml"):
        load_settings({DATA_ROOT_ENV: str(tmp_path)})


def test_invalid_toml_fails(tmp_path: Path) -> None:
    write_config(tmp_path, "[consumer\nworkers = 2\n")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_settings({DATA_ROOT_ENV: str(tmp_path)})


@pytest.mark.parametrize("body", ["", "[consumer]\n", "consumer = 2\n"])
def test_missing_workers_fails(tmp_path: Path, body: str) -> None:
    write_config(tmp_path, body)
    with pytest.raises(ConfigError, match="workers is required"):
        load_settings({DATA_ROOT_ENV: str(tmp_path)})


@pytest.mark.parametrize("value", ["0", "-1", "true", '"2"', "2.0"])
def test_invalid_workers_fails(tmp_path: Path, value: str) -> None:
    write_config(tmp_path, f"[consumer]\nworkers = {value}\n")
    with pytest.raises(ConfigError, match="integer >= 1"):
        load_settings({DATA_ROOT_ENV: str(tmp_path)})


def test_ensure_dirs_creates_logs(tmp_path: Path) -> None:
    settings = Settings(data_root=tmp_path, workers=1)
    settings.ensure_dirs()
    assert settings.logs_dir.is_dir()
