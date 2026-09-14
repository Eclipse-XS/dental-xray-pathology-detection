import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dental_xray_service.api.routes import health, models, predictions
from dental_xray_service.db.base import Base
from dental_xray_service.db.session import create_session_factory
from dental_xray_service.inference.base import InferenceBackend
from dental_xray_service.inference.postprocessing import DetectionPostprocessor
from dental_xray_service.inference.preprocessing import ImagePreprocessor
from dental_xray_service.inference.service import InferenceService
from dental_xray_service.inference.types import DetectionResult
from dental_xray_service.storage.local import NullObjectStorage


class FakeBackend(InferenceBackend):
    def predict(self, image):
        return DetectionResult(np.array([[1, 2, 30, 40]]), np.array([0.9]), np.array([1]))

    def warmup(self):
        pass

    def metadata(self):
        return {
            "experiment_id": "F_final_fcos_tuned",
            "model_version": "test",
            "architecture": "FCOS ResNet50 FPN",
            "image_size": 768,
            "class_names": {0: "Impacted", 1: "Caries", 2: "Periapical Lesion", 3: "Deep Caries"},
            "backend": "fake",
            "artifact_sha256": "a" * 64,
            "runtime": "test",
        }


def test_health_model_info_and_prediction(tmp_path, png_bytes):
    app = FastAPI()
    for router in (health.router, models.router, predictions.router):
        app.include_router(router, prefix="/api/v1")
    engine, factory = create_session_factory(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    app.state.ready = True
    app.state.session_factory = factory
    app.state.inference_service = InferenceService(
        FakeBackend(),
        ImagePreprocessor(1_000_000, 64, 1024),
        DetectionPostprocessor(0.5),
        NullObjectStorage(),
        factory,
    )
    client = TestClient(app)
    assert client.get("/api/v1/health").status_code == 200
    app.state.ready = False
    assert client.get("/api/v1/ready").status_code == 503
    app.state.ready = True
    assert client.get("/api/v1/ready").status_code == 200
    assert client.get("/api/v1/model-info").json()["experiment_id"] == "F_final_fcos_tuned"
    response = client.post("/api/v1/predict", files={"file": ("x.png", png_bytes, "image/png")})
    assert response.status_code == 200
    assert response.json()["detections"][0]["class_name"] == "Impacted"
