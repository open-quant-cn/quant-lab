import fcntl
import os
import signal
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from huey import Huey

from app.config import Settings

PARENT_POLL_SECONDS = 1.0


class LockHeld(RuntimeError):
    pass


@contextmanager
def hold_lock(path: Path) -> Iterator[None]:
    """Hold an exclusive flock on path; raise LockHeld if another holder exists."""
    with path.open("a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise LockHeld(f"lock already held: {path}") from exc
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def stop_when_parent_exits(parent_pid: int) -> None:
    """Shut the consumer down gracefully once serve is gone, even after a SIGKILL."""

    def watch() -> None:
        while os.getppid() == parent_pid:
            time.sleep(PARENT_POLL_SECONDS)
        os.kill(os.getpid(), signal.SIGINT)

    threading.Thread(target=watch, daemon=True).start()


def run_consumer(huey: Huey, settings: Settings, parent_pid: int | None) -> None:
    with hold_lock(settings.consumer_lock):
        if parent_pid is not None:
            stop_when_parent_exits(parent_pid)
        huey.create_consumer(workers=settings.workers, worker_type="thread").run()
