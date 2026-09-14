from pathlib import Path

from dental_xray_service.core.exceptions import StorageError

from .base import ObjectStorage


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def save(self, prediction_id: str, payload: bytes, content_type: str) -> str:
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            target = self.root / f"{prediction_id}{suffix}"
            target.write_bytes(payload)
            return target.as_uri()
        except OSError as exc:
            raise StorageError("Could not store uploaded image") from exc


class NullObjectStorage(ObjectStorage):
    def save(self, prediction_id: str, payload: bytes, content_type: str) -> None:
        return None
