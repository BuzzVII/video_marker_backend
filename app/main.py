from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.image_sets import router as image_sets_router
from app.api.videos import router as videos_router
from app.core.config import settings
from app.services.storage import ensure_data_dirs


def create_app() -> FastAPI:
    ensure_data_dirs()

    app = FastAPI(
        title="House Marker API",
        version="0.1.0",
        description="Backend for extracting video frames and saving point and line correspondences.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(image_sets_router)
    app.include_router(videos_router)

    return app


app = create_app()
