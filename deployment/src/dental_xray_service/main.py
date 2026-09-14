import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dental_xray_service.api.routes import health, metrics, models, predictions
from dental_xray_service.core.config import get_settings
from dental_xray_service.core.exceptions import InvalidImageError, ServiceError
from dental_xray_service.core.logging import configure_logging, correlation_id
from dental_xray_service.db.base import Base
from dental_xray_service.db.session import create_session_factory
from dental_xray_service.inference.factory import create_backend
from dental_xray_service.inference.postprocessing import DetectionPostprocessor
from dental_xray_service.inference.preprocessing import ImagePreprocessor
from dental_xray_service.inference.service import InferenceService
from dental_xray_service.monitoring.middleware import CorrelationIdMiddleware
from dental_xray_service.storage.factory import create_storage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.ready = False
    engine, session_factory = create_session_factory(settings.database_url)
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
    backend = create_backend(settings)
    backend.warmup()
    app.state.session_factory = session_factory
    app.state.inference_service = InferenceService(
        backend,
        ImagePreprocessor(
            settings.max_upload_bytes,
            settings.min_image_dimension,
            settings.max_image_dimension,
            settings.image_size,
        ),
        DetectionPostprocessor(settings.confidence_threshold),
        create_storage(settings),
        session_factory,
        settings.persist_predictions,
    )
    app.state.ready = True
    logger.info("service_ready", extra={"backend": settings.backend})
    try:
        yield
    finally:
        app.state.ready = False
        backend.close()
        engine.dispose()


app = FastAPI(
    title="Dental X-ray Pathology Detection API",
    version="0.1.0",
    description="Experimental research inference API; not intended for clinical diagnosis or medical decisions.",
    lifespan=lifespan,
)
app.add_middleware(CorrelationIdMiddleware)
for router in (health.router, models.router, predictions.router, metrics.router):
    app.include_router(router, prefix="/api/v1")


@app.exception_handler(InvalidImageError)
async def invalid_image_handler(request: Request, exc: InvalidImageError):
    return JSONResponse(status_code=422, content={"detail": str(exc), "correlation_id": correlation_id.get()})


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    logger.exception("service_error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Request could not be completed", "correlation_id": correlation_id.get()},
    )
