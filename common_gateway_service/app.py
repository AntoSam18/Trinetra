from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common_gateway_service.api.router import api_router
from common_gateway_service.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="Trinetra Common Gateway Service", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin] if settings.frontend_origin else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    return app
