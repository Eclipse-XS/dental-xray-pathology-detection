from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from dental_xray_service.api.dependencies import get_inference_service, get_session_factory
from dental_xray_service.api.schemas.prediction import PredictionResponse, StoredPredictionResponse
from dental_xray_service.db.repositories import PredictionRepository
from dental_xray_service.inference.service import InferenceService

router = APIRouter(tags=["predictions"])


def _stored(record) -> dict:
    return {
        "prediction_id": record.id,
        "created_at": record.created_at,
        "backend": record.backend,
        "latency_ms": record.latency_ms,
        "image": {"width": record.image_width, "height": record.image_height},
        "detections": [
            {
                "class_id": d.class_id,
                "class_name": d.class_name,
                "score": d.score,
                "box": (d.x1, d.y1, d.x2, d.y2),
            }
            for d in record.detections
        ],
    }


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...), service: InferenceService = Depends(get_inference_service)
) -> dict:
    chunks, size = [], 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > service.preprocessor.max_bytes:
            from dental_xray_service.core.exceptions import InvalidImageError

            raise InvalidImageError(f"Image exceeds {service.preprocessor.max_bytes} byte limit")
        chunks.append(chunk)
    payload = b"".join(chunks)
    return service.predict(payload, file.content_type or "application/octet-stream")


@router.get("/predictions/{prediction_id}", response_model=StoredPredictionResponse)
def get_prediction(prediction_id: str, session_factory=Depends(get_session_factory)) -> dict:
    with session_factory() as session:
        record = PredictionRepository(session).get(prediction_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Prediction not found")
        return _stored(record)


@router.get("/predictions", response_model=list[StoredPredictionResponse])
def list_predictions(
    limit: int = Query(50, ge=1, le=200),
    before: datetime | None = None,
    session_factory=Depends(get_session_factory),
) -> list[dict]:
    with session_factory() as session:
        return [_stored(record) for record in PredictionRepository(session).list(limit, before)]
