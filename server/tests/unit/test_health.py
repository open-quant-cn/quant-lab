from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_healthz_returns_ok(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(data_root=tmp_path, workers=1)))
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
