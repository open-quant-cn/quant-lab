from fastapi import FastAPI

from app.api.routes import health
from app.config import Settings


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(title="quant-lab")
    app.state.settings = settings
    app.include_router(health.router)
    return app
