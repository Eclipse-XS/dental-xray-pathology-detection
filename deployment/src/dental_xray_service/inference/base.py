from abc import ABC, abstractmethod
from typing import Any

from .types import DetectionResult, PreparedImage


class InferenceBackend(ABC):
    @abstractmethod
    def predict(self, image: PreparedImage) -> DetectionResult:
        raise NotImplementedError

    @abstractmethod
    def warmup(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def metadata(self) -> dict[str, Any]:
        raise NotImplementedError

    def close(self) -> None:
        return None
