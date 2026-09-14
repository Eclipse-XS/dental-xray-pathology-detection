from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from dental_xray_service.core.exceptions import PersistenceError
from dental_xray_service.inference.types import Detection

from .entities import DetectionEntity, ModelVersion, PredictionRequest


class PredictionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_model_version(self, metadata: dict) -> ModelVersion:
        version = self.session.scalar(
            select(ModelVersion).where(ModelVersion.model_version == metadata["model_version"])
        )
        if version:
            return version
        version = ModelVersion(
            experiment_id=metadata["experiment_id"],
            model_version=metadata["model_version"],
            architecture=metadata["architecture"],
            backend=metadata["backend"],
            artifact_sha256=metadata["artifact_sha256"],
            runtime=metadata["runtime"],
            metadata_json=metadata,
        )
        self.session.add(version)
        self.session.flush()
        return version

    def save(
        self,
        *,
        prediction_id: str,
        correlation_id: str,
        metadata: dict,
        width: int,
        height: int,
        content_type: str,
        storage_uri: str | None,
        latency_ms: float,
        detections: list[Detection],
    ) -> PredictionRequest:
        try:
            version = self.ensure_model_version(metadata)
            request = PredictionRequest(
                id=prediction_id,
                correlation_id=correlation_id,
                model_version_id=version.id,
                backend=metadata["backend"],
                image_width=width,
                image_height=height,
                content_type=content_type,
                storage_uri=storage_uri,
                latency_ms=latency_ms,
            )
            request.detections = [
                DetectionEntity(
                    class_id=d.class_id,
                    class_name=d.class_name,
                    score=d.score,
                    x1=d.box[0],
                    y1=d.box[1],
                    x2=d.box[2],
                    y2=d.box[3],
                )
                for d in detections
            ]
            self.session.add(request)
            self.session.commit()
            self.session.refresh(request)
            return request
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise PersistenceError("Could not persist prediction") from exc

    def get(self, prediction_id: str) -> PredictionRequest | None:
        return self.session.get(PredictionRequest, prediction_id)

    def list(self, limit: int = 50, before: datetime | None = None) -> list[PredictionRequest]:
        statement = select(PredictionRequest).order_by(desc(PredictionRequest.created_at)).limit(limit)
        if before is not None:
            statement = statement.where(PredictionRequest.created_at < before)
        return list(self.session.scalars(statement).all())
