import os
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[2]
STARTUP_TIMEOUT = 20


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def run_app(data_root: Path, *args: str) -> subprocess.Popen[bytes]:
    env = {**os.environ, "QUANT_LAB_DATA_ROOT": str(data_root)}
    return subprocess.Popen(
        [sys.executable, "-m", "app", *args],
        cwd=SERVER_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def wait_healthy(port: int, proc: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        assert proc.poll() is None, proc.stdout.read().decode() if proc.stdout else ""
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as r:
                if r.status == 200:
                    return
        except OSError:
            time.sleep(0.2)
    raise AssertionError("serve did not become healthy")


def table_names(app_db: Path) -> set[str]:
    with sqlite3.connect(app_db) as conn:
        rows = conn.execute("select name from sqlite_master where type = 'table'")
        return {name for (name,) in rows}


def write_config(data_root: Path) -> None:
    (data_root / "config.toml").write_text("[consumer]\nworkers = 2\n")


def wait_consumer_lock_free(data_root: Path) -> None:
    """A fresh consumer that keeps running means it got the lock; stop it again."""
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        probe = run_app(data_root, "consumer")
        try:
            out, _ = probe.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            probe.send_signal(signal.SIGINT)
            probe.wait(timeout=STARTUP_TIMEOUT)
            return
        assert b"another consumer is running" in out, out.decode()
    raise AssertionError("consumer lock was never released")


@pytest.mark.parametrize("stop_signal", [signal.SIGINT, signal.SIGTERM])
def test_serve_starts_api_and_single_consumer(tmp_path: Path, stop_signal: int) -> None:
    write_config(tmp_path)
    port = free_port()
    serve = run_app(tmp_path, "serve", "--port", str(port))
    try:
        wait_healthy(port, serve)
        assert {"alembic_version", "task", "schedule", "kv"} <= table_names(tmp_path / "app.db")

        # The consumer started by serve holds the lock, so a second one must refuse.
        deadline = time.monotonic() + STARTUP_TIMEOUT
        while True:
            second = run_app(tmp_path, "consumer")
            out, _ = second.communicate(timeout=STARTUP_TIMEOUT)
            if second.returncode == 1 and b"another consumer is running" in out:
                break
            assert time.monotonic() < deadline, out.decode()
            time.sleep(0.2)

        # A second serve must also refuse instead of starting a duplicate scheduler.
        dup = run_app(tmp_path, "serve", "--port", str(free_port()))
        out, _ = dup.communicate(timeout=STARTUP_TIMEOUT)
        assert dup.returncode == 1, out.decode()
    finally:
        serve.send_signal(stop_signal)
        serve.wait(timeout=STARTUP_TIMEOUT)
    assert serve.returncode == 0

    wait_consumer_lock_free(tmp_path)


def test_consumer_stops_when_serve_is_killed(tmp_path: Path) -> None:
    write_config(tmp_path)
    port = free_port()
    serve = run_app(tmp_path, "serve", "--port", str(port))
    try:
        wait_healthy(port, serve)
    finally:
        serve.kill()
        serve.wait(timeout=STARTUP_TIMEOUT)
    wait_consumer_lock_free(tmp_path)
