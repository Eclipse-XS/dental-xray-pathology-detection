from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    @abstractmethod
    def save(self, prediction_id: str, payload: bytes, content_type: str) -> str | None:
        raise NotImplementedError
