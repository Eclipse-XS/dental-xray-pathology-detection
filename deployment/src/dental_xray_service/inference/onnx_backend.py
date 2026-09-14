from typing import Any

import numpy as np

from dental_xray_service.core.exceptions import InferenceError
from dental_xray_service.models.metadata import load_model_identity

from .base import InferenceBackend
from .types import DetectionResult, PreparedImage, SpatialTransform


class ONNXRuntimeBackend(InferenceBackend):
    def __init__(self, model_path, metadata_path, device: str, image_size: int) -> None:
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise RuntimeError("Install the 'onnx' deployment extra") from exc
        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device.startswith("cuda")
            else ["CPUExecutionProvider"]
        )
        available = set(ort.get_available_providers())
        selected = [p for p in providers if p in available]
        if not selected:
            raise RuntimeError(f"No requested ONNX Runtime provider is available: {providers}")
        model_path = model_path.resolve()
        if not model_path.is_file():
            raise FileNotFoundError(model_path)
        self.session = ort.InferenceSession(str(model_path), providers=selected)
        self.image_size = image_size
        self._metadata = load_model_identity(metadata_path.resolve(), model_path, "onnx")
        self._metadata.update(
            runtime=f"onnxruntime-{ort.__version__}", providers=self.session.get_providers()
        )

    def predict(self, image: PreparedImage) -> DetectionResult:
        tensor = image.tensor
        if tensor.shape != (3, self.image_size, self.image_size):
            raise InferenceError(f"Expected canonical tensor shape (3, {self.image_size}, {self.image_size})")
        try:
            boxes, scores, labels, count = self.session.run(None, {"image": tensor})
        except Exception as exc:
            raise InferenceError("ONNX Runtime inference failed") from exc
        n = int(np.asarray(count).item())
        return DetectionResult(boxes[:n], scores[:n], labels[:n], {"backend": "onnx"})

    def warmup(self) -> None:
        sample = np.zeros((3, self.image_size, self.image_size), np.float32)
        self.predict(
            PreparedImage(
                sample,
                self.image_size,
                self.image_size,
                "image/png",
                SpatialTransform(1, 0, 0, self.image_size, self.image_size, self.image_size),
            )
        )

    def metadata(self) -> dict[str, Any]:
        return dict(self._metadata)
