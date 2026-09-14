from io import BytesIO

import numpy as np
from PIL import Image, UnidentifiedImageError

from dental_xray_service.core.exceptions import InvalidImageError

from .types import PreparedImage, SpatialTransform

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImagePreprocessor:
    """Decode as RGB and produce CHW float32 [0, 1], matching final evaluation."""

    def __init__(self, max_bytes: int, min_dimension: int, max_dimension: int, image_size: int = 768) -> None:
        self.max_bytes = max_bytes
        self.min_dimension = min_dimension
        self.max_dimension = max_dimension
        self.image_size = image_size

    def prepare(self, payload: bytes, content_type: str) -> PreparedImage:
        if content_type not in ALLOWED_MIME_TYPES:
            raise InvalidImageError(f"Unsupported content type: {content_type}")
        if not payload:
            raise InvalidImageError("Uploaded image is empty")
        if len(payload) > self.max_bytes:
            raise InvalidImageError(f"Image exceeds {self.max_bytes} byte limit")
        try:
            with Image.open(BytesIO(payload)) as source:
                source.verify()
            with Image.open(BytesIO(payload)) as source:
                image = source.convert("RGB")
                width, height = image.size
                if min(width, height) < self.min_dimension or max(width, height) > self.max_dimension:
                    raise InvalidImageError(f"Image dimensions {width}x{height} are outside allowed range")
                scale = min(self.image_size / width, self.image_size / height)
                resized_width = max(1, round(width * scale))
                resized_height = max(1, round(height * scale))
                resized = image.resize((resized_width, resized_height), Image.Resampling.BILINEAR)
                array = np.empty((self.image_size, self.image_size, 3), dtype=np.float32)
                array[...] = np.array([0.485, 0.456, 0.406], dtype=np.float32)
                array[:resized_height, :resized_width] = np.asarray(resized, dtype=np.float32) / 255.0
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidImageError("Image could not be decoded") from exc
        return PreparedImage(
            tensor=np.transpose(array, (2, 0, 1)).copy(),
            original_width=width,
            original_height=height,
            content_type=content_type,
            transform=SpatialTransform(scale, 0, 0, resized_width, resized_height, self.image_size),
        )
