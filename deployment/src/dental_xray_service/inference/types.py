from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class SpatialTransform:
    scale: float
    pad_left: int
    pad_top: int
    resized_width: int
    resized_height: int
    canvas_size: int


@dataclass(frozen=True)
class PreparedImage:
    tensor: np.ndarray
    original_width: int
    original_height: int
    content_type: str
    transform: SpatialTransform


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    score: float
    box: tuple[float, float, float, float]


@dataclass(frozen=True)
class DetectionResult:
    boxes: np.ndarray
    scores: np.ndarray
    labels: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)
