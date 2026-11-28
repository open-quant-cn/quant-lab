from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture

from app.cli import build_parser, main

COMMANDS = ["serve", "ingest", "clean", "factor", "signal", "backup"]


@pytest.mark.parametrize("command", COMMANDS)
def test_cli_accepts_every_pipeline_stage(command: str) -> None:
    args = build_parser().parse_args([command])
    assert args.command == command


def test_cli_rejects_unknown_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["trade"])
    assert excinfo.value.code == 2


def test_cli_unimplemented_command_exits_nonzero(capsys: CaptureFixture[str]) -> None:
    assert main(["ingest"]) == 1
    assert "not implemented yet: ingest" in capsys.readouterr().out


@pytest.mark.parametrize("command", ["serve", "consumer"])
def test_service_commands_fail_without_config(
    command: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    monkeypatch.setenv("QUANT_LAB_DATA_ROOT", str(tmp_path))
    assert main([command]) == 1
    assert "config error: missing" in capsys.readouterr().err
    assert not (tmp_path / "app.db").exists()
