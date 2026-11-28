#!/usr/bin/env bash
# Single entry point for every local check. CI runs the same script.
set -euo pipefail
cd "$(dirname "$0")/.."

uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest -q
