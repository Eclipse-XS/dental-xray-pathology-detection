import logging
import time
import uuid
from dataclasses import asdict

from dental_xray_service.core.logging import correlation_id
from dental_xray_service.db.repositories import PredictionRepository
from dental_xray_service.monitoring.metrics import DETECTIONS, INFERENCE_LATENCY, PREDICTIONS
from dental_xray_service.storage.base import ObjectStorage

from .base import InferenceBackend
from .postprocessing import DetectionPostprocessor
from .preprocessing import ImagePreprocessor

logger = logging.getLogger(__name__)


class InferenceService:
    def __init__(
        self,
        backend: InferenceBackend,
        preprocessor: ImagePreprocessor,
        postprocessor: DetectionPostprocessor,
        storage: ObjectStorage,
        session_factory=None,
        persist: bool = True,
    ) -> None:
        self.backend = backend
        self.preprocessor = preprocessor
        self.postprocessor = postprocessor
        self.storage = storage
        self.session_factory = session_factory
        self.persist = persist

    def predict(self, payload: bytes, content_type: str) -> dict:
        prediction_id = str(uuid.uuid4())
        image = self.preprocessor.prepare(payload, content_type)
        backend_name = self.backend.metadata()["backend"]
        started = time.perf_counter()
        try:
            raw = self.backend.predict(image)
            detections = self.postprocessor.apply(raw, image)
            latency_ms = (time.perf_counter() - started) * 1000
            storage_uri = self.storage.save(prediction_id, payload, content_type)
            if self.persist and self.session_factory is not None:
                with self.session_factory() as session:
                    PredictionRepository(session).save(
                        prediction_id=prediction_id,
                        correlation_id=correlation_id.get(),
                        metadata=self.backend.metadata(),
                        width=image.original_width,
                        height=image.original_height,
                        content_type=content_type,
                        storage_uri=storage_uri,
                        latency_ms=latency_ms,
                        detections=detections,
                    )
            PREDICTIONS.labels(backend_name, "success").inc()
            INFERENCE_LATENCY.labels(backend_name).observe(latency_ms / 1000)
            for detection in detections:
                DETECTIONS.labels(detection.class_name).inc()
            logger.info(
                "prediction_completed",
                extra={
                    "prediction_id": prediction_id,
                    "backend": backend_name,
                    "model_version": self.backend.metadata()["model_version"],
                    "latency_ms": round(latency_ms, 3),
                    "detection_count": len(detections),
                    "status": "success",
                },
            )
            return {
                "prediction_id": prediction_id,
                "model": self.backend.metadata(),
                "image": {"width": image.original_width, "height": image.original_height},
                "latency_ms": latency_ms,
                "detections": [asdict(d) for d in detections],
            }
        except Exception as exc:
            PREDICTIONS.labels(backend_name, "error").inc()
            logger.exception(
                "prediction_failed",
                extra={
                    "prediction_id": prediction_id,
                    "backend": backend_name,
                    "model_version": self.backend.metadata()["model_version"],
                    "status": "error",
                    "error_type": type(exc).__name__,
                },
            )
            raise
