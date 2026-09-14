import numpy as np

from dental_xray_service.inference.base import InferenceBackend
from dental_xray_service.inference.types import DetectionResult, PreparedImage, SpatialTransform


class FakeBackend(InferenceBackend):
    def predict(self, image):
        return DetectionResult(np.empty((0, 4)), np.empty(0), np.empty(0, dtype=int))

    def warmup(self):
        return None

    def metadata(self):
        return {"backend": "fake"}


def test_backend_contract_is_usable():
    backend = FakeBackend()
    result = backend.predict(
        PreparedImage(np.zeros((3, 8, 8)), 8, 8, "image/png", SpatialTransform(1, 0, 0, 8, 8, 8))
    )
    assert result.boxes.shape == (0, 4)
    assert backend.metadata()["backend"] == "fake"
