import threading
from pathlib import Path

import pytest

from app.workflow.consumer import LockHeld, hold_lock


def test_second_holder_is_rejected(tmp_path: Path) -> None:
    lock = tmp_path / "consumer.lock"
    with hold_lock(lock), pytest.raises(LockHeld), hold_lock(lock):
        pass


def test_lock_is_reusable_after_release(tmp_path: Path) -> None:
    lock = tmp_path / "consumer.lock"
    with hold_lock(lock):
        pass
    with hold_lock(lock):
        pass


def test_lock_blocks_another_thread(tmp_path: Path) -> None:
    # Workers are threads, so the lock must exclude threads of the same process.
    lock = tmp_path / "consumer.lock"
    errors: list[BaseException] = []

    def contend() -> None:
        try:
            with hold_lock(lock):
                pass
        except LockHeld as exc:
            errors.append(exc)

    with hold_lock(lock):
        thread = threading.Thread(target=contend)
        thread.start()
        thread.join()
    assert len(errors) == 1
