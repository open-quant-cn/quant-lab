import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn

from app.config import TIMEZONE, ConfigError, Settings, load_settings
from app.main import create_app
from app.schema.migrate import upgrade_to_head
from app.workflow.consumer import LockHeld, hold_lock, run_consumer
from app.workflow.tasks import huey, initialize_queue_schema

SERVER_DIR = Path(__file__).resolve().parents[1]
CONSUMER_STOP_TIMEOUT = 30


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quant-lab", description="Personal A-share quant pipeline."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve", help="Run the FastAPI service with the scheduler.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    consumer = sub.add_parser("consumer", help="Run the Huey consumer (normally started by serve).")
    consumer.add_argument("--parent-pid", type=int, help="Exit once this process is gone.")
    sub.add_parser("ingest", help="Fetch Tushare data into the raw layer.")
    sub.add_parser("clean", help="Clean the raw layer and publish to the lake.")
    sub.add_parser("factor", help="Compute registered factors.")
    sub.add_parser("signal", help="Generate the daily signal.")
    sub.add_parser("backup", help="Checkpoint and back up the lake.")
    return parser


def use_beijing_time() -> None:
    # Huey with utc=False schedules by datetime.now(), so pin the process timezone.
    os.environ["TZ"] = TIMEZONE
    time.tzset()


def serve(settings: Settings, host: str, port: int) -> int:
    # Fail fast instead of starting an API whose consumer would exit at once.
    try:
        with hold_lock(settings.consumer_lock):
            pass
    except LockHeld as exc:
        print(f"another consumer is running: {exc}", file=sys.stderr)
        return 1

    upgrade_to_head(settings.app_db)
    initialize_queue_schema()

    server = uvicorn.Server(uvicorn.Config(create_app(settings), host=host, port=port))

    # uvicorn restores the previous handlers on shutdown and re-raises the captured
    # signal. With the default handlers that kills serve before the consumer is
    # stopped (SIGTERM) or exits via KeyboardInterrupt (SIGINT), so install ours.
    def request_exit(_sig: int, _frame: object) -> None:
        server.should_exit = True

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, request_exit)

    # Own process group: a terminal Ctrl-C reaches only serve, which stops the consumer.
    consumer = subprocess.Popen(
        [sys.executable, "-m", "app", "consumer", "--parent-pid", str(os.getpid())],
        cwd=SERVER_DIR,
        env=os.environ.copy(),
        process_group=0,
    )
    stopping = threading.Event()
    consumer_died = threading.Event()

    def watch_consumer() -> None:
        consumer.wait()
        if not stopping.is_set():
            print(f"consumer exited unexpectedly (code {consumer.returncode})", file=sys.stderr)
            consumer_died.set()
            server.should_exit = True

    threading.Thread(target=watch_consumer, daemon=True).start()
    try:
        server.run()
    finally:
        stopping.set()
        if consumer.poll() is None:
            consumer.send_signal(signal.SIGINT)  # graceful shutdown in Huey
            try:
                consumer.wait(timeout=CONSUMER_STOP_TIMEOUT)
            except subprocess.TimeoutExpired:
                consumer.kill()
                consumer.wait()
    return 1 if consumer_died.is_set() else 0


def consume(settings: Settings, parent_pid: int | None) -> int:
    try:
        run_consumer(huey, settings, parent_pid)
    except LockHeld as exc:
        print(f"another consumer is running: {exc}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    use_beijing_time()
    if args.command in ("serve", "consumer"):
        try:
            settings = load_settings()
        except ConfigError as exc:
            print(f"config error: {exc}", file=sys.stderr)
            return 1
        settings.ensure_dirs()
        if args.command == "serve":
            return serve(settings, args.host, args.port)
        return consume(settings, args.parent_pid)
    print(f"not implemented yet: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
