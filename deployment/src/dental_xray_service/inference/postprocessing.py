import numpy as np

from dental_xray_service.core.constants import CLASS_NAMES, MODEL_LABEL_OFFSET

from .types import Detection, DetectionResult, PreparedImage


class DetectionPostprocessor:
    def __init__(self, confidence_threshold: float) -> None:
        if not 0 <= confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be in [0, 1]")
        self.threshold = confidence_threshold

    def apply(self, result: DetectionResult, image: PreparedImage) -> list[Detection]:
        detections: list[Detection] = []
        for box, score, model_label in zip(result.boxes, result.scores, result.labels, strict=True):
            if float(score) < self.threshold:
                continue
            class_id = int(model_label) - MODEL_LABEL_OFFSET
            if class_id not in CLASS_NAMES:
                continue
            x1, y1, x2, y2 = np.asarray(box, dtype=float).tolist()
            transform = image.transform
            x1 = (x1 - transform.pad_left) / transform.scale
            x2 = (x2 - transform.pad_left) / transform.scale
            y1 = (y1 - transform.pad_top) / transform.scale
            y2 = (y2 - transform.pad_top) / transform.scale
            clipped = (
                max(0.0, min(x1, image.original_width)),
                max(0.0, min(y1, image.original_height)),
                max(0.0, min(x2, image.original_width)),
                max(0.0, min(y2, image.original_height)),
            )
            if clipped[2] <= clipped[0] or clipped[3] <= clipped[1]:
                continue
            detections.append(Detection(class_id, CLASS_NAMES[class_id], float(score), clipped))
        return detections
