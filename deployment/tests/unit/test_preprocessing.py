import numpy as np
import pytest

from dental_xray_service.core.exceptions import InvalidImageError
from dental_xray_service.inference.preprocessing import ImagePreprocessor


def test_preprocessing_matches_final_evaluation_contract(png_bytes):
    result = ImagePreprocessor(1_000_000, 64, 1024).prepare(png_bytes, "image/png")
    assert result.tensor.shape == (3, 768, 768)
    assert result.tensor.dtype == np.float32
    assert 0 <= result.tensor.min() <= result.tensor.max() <= 1
    assert (result.original_width, result.original_height) == (128, 96)
    assert result.transform.scale == 6
    assert (result.transform.resized_width, result.transform.resized_height) == (768, 576)


@pytest.mark.parametrize("payload,mime", [(b"bad", "image/png"), (b"x", "text/plain")])
def test_rejects_invalid_upload(payload, mime):
    with pytest.raises(InvalidImageError):
        ImagePreprocessor(1000, 64, 1024).prepare(payload, mime)
