
import pytest
from pydantic import ValidationError

from dental_xray_service.core.config import Settings


def test_missing_configured_onnx_artifact_fails_at_startup(tmp_path):
    with pytest.raises(ValidationError, match="artifact does not exist"):
        Settings(backend="onnx", onnx_model_path=tmp_path / "missing.onnx")


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValidationError):
        Settings(confidence_threshold=1.1)
