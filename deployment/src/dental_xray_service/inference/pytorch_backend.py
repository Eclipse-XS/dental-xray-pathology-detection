from typing import Any

import numpy as np
import torch

from dental_xray_service.core.exceptions import InferenceError
from dental_xray_service.models.fcos import build_final_fcos
from dental_xray_service.models.metadata import load_model_identity

from .base import InferenceBackend
from .types import DetectionResult, PreparedImage, SpatialTransform


class PyTorchBackend(InferenceBackend):
    def __init__(self, checkpoint_path, metadata_path, device: str, image_size: int) -> None:
        self.device = torch.device(device)
        checkpoint_path = checkpoint_path.resolve()
        if not checkpoint_path.is_file():
            raise FileNotFoundError(checkpoint_path)
        self.model = build_final_fcos(image_size)
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        state = checkpoint.get("model_state_dict", checkpoint)
        self.model.load_state_dict(state, strict=True)
        self.model.to(self.device).eval()
        self._metadata = load_model_identity(metadata_path.resolve(), checkpoint_path, "pytorch")
        self._metadata["runtime"] = f"torch-{torch.__version__}"

    def predict(self, image: PreparedImage) -> DetectionResult:
        tensor = torch.from_numpy(image.tensor).to(self.device)
        try:
            with torch.inference_mode():
                output = self.model([tensor])[0]
        except Exception as exc:
            raise InferenceError("PyTorch inference failed") from exc
        return DetectionResult(
            boxes=output["boxes"].detach().cpu().numpy(),
            scores=output["scores"].detach().cpu().numpy(),
            labels=output["labels"].detach().cpu().numpy(),
            metadata={"backend": "pytorch"},
        )

    def warmup(self) -> None:
        size = self._metadata["image_size"]
        sample = np.zeros((3, size, size), np.float32)
        self.predict(
            PreparedImage(sample, size, size, "image/png", SpatialTransform(1, 0, 0, size, size, size))
        )

    def metadata(self) -> dict[str, Any]:
        return dict(self._metadata)
