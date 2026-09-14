from datetime import datetime

from pydantic import BaseModel, Field


class Box(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionResponse(BaseModel):
    class_id: int
    class_name: str
    score: float = Field(ge=0, le=1)
    box: tuple[float, float, float, float]


class ImageInfo(BaseModel):
    width: int
    height: int


class PredictionResponse(BaseModel):
    prediction_id: str
    model: dict
    image: ImageInfo
    latency_ms: float
    detections: list[DetectionResponse]


class StoredPredictionResponse(BaseModel):
    prediction_id: str
    created_at: datetime
    backend: str
    latency_ms: float
    image: ImageInfo
    detections: list[DetectionResponse]
