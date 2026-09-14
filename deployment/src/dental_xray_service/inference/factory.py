from dental_xray_service.core.config import Settings

from .base import InferenceBackend
from .onnx_backend import ONNXRuntimeBackend
from .pytorch_backend import PyTorchBackend


def create_backend(settings: Settings) -> InferenceBackend:
    """The single backend-selection branch in the application."""
    if settings.backend == "pytorch":
        return PyTorchBackend(
            settings.checkpoint_path,
            settings.model_metadata_path,
            settings.device,
            settings.image_size,
        )
    if settings.backend == "onnx":
        return ONNXRuntimeBackend(
            settings.onnx_model_path,
            settings.model_metadata_path,
            settings.device,
            settings.image_size,
        )
    raise ValueError(f"Unsupported backend: {settings.backend}")
