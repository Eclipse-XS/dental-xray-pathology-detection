import numpy as np

from dental_xray_service.inference.postprocessing import DetectionPostprocessor
from dental_xray_service.inference.types import DetectionResult, PreparedImage, SpatialTransform


def test_filters_maps_and_clips_detections():
    raw = DetectionResult(
        boxes=np.array([[-1, 2, 20, 30], [1, 1, 3, 3]], np.float32),
        scores=np.array([0.8, 0.2], np.float32),
        labels=np.array([1, 2]),
    )
    image = PreparedImage(
        np.zeros((3, 768, 768)), 10, 15, "image/png", SpatialTransform(2, 0, 0, 20, 30, 768)
    )
    result = DetectionPostprocessor(0.5).apply(raw, image)
    assert len(result) == 1
    assert result[0].class_id == 0
    assert result[0].class_name == "Impacted"
    assert result[0].box == (0.0, 1.0, 10.0, 15.0)
