from io import BytesIO

import numpy as np
import pytest
from PIL import Image

from dental_xray_service.inference.postprocessing import DetectionPostprocessor
from dental_xray_service.inference.preprocessing import ImagePreprocessor
from dental_xray_service.inference.types import DetectionResult


@pytest.mark.parametrize("size", [(200, 200), (301, 127), (127, 301), (333, 257)])
def test_letterbox_and_inverse_coordinates(size):
    stream = BytesIO()
    Image.new("RGB", size, "white").save(stream, "PNG")
    prepared = ImagePreprocessor(1_000_000, 32, 1024, 768).prepare(stream.getvalue(), "image/png")
    assert prepared.tensor.shape == (3, 768, 768)
    assert prepared.transform.resized_width <= 768 and prepared.transform.resized_height <= 768
    original = np.array([10.0, 11.0, size[0] - 7.0, size[1] - 5.0])
    model_box = original * prepared.transform.scale
    raw = DetectionResult(model_box.reshape(1, 4), np.array([0.9]), np.array([1]))
    restored = DetectionPostprocessor(0.5).apply(raw, prepared)[0].box
    assert np.allclose(restored, original)
    assert 0 <= restored[0] < restored[2] <= size[0]
    assert 0 <= restored[1] < restored[3] <= size[1]
