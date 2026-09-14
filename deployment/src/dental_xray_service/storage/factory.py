from dental_xray_service.core.config import Settings

from .base import ObjectStorage
from .local import LocalObjectStorage, NullObjectStorage
from .minio import MinioObjectStorage


def create_storage(settings: Settings) -> ObjectStorage:
    if settings.storage_backend == "local":
        return LocalObjectStorage(settings.storage_path)
    if settings.storage_backend == "minio":
        return MinioObjectStorage(
            settings.minio_endpoint,
            settings.minio_access_key,
            settings.minio_secret_key,
            settings.minio_bucket,
        )
    return NullObjectStorage()
