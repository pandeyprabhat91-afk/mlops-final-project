"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.logging_config import setup_logging
from backend.app.model_loader import load_model
from backend.app.routers.admin import admin_router
from backend.app.routers.pipeline import pipeline_router
from backend.app.routers.predict import router
from backend.app.routers.support import support_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup."""
    setup_logging()
    load_model()
    yield


app = FastAPI(
    title="Deepfake Detection API",
    description="Classify MP4 videos as real or fake using CNN+LSTM model",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(pipeline_router, prefix="/pipeline")
app.include_router(admin_router)
app.include_router(support_router)
