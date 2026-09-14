from dental_xray_service.core.exceptions import StorageError

from .base import ObjectStorage


class MinioObjectStorage(ObjectStorage):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        try:
            from minio import Minio
        except ImportError as exc:
            raise RuntimeError("Install the 'storage' deployment extra") from exc
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self.bucket = bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def save(self, prediction_id: str, payload: bytes, content_type: str) -> str:
        from io import BytesIO

        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[content_type]
        name = f"{prediction_id}{suffix}"
        try:
            self.client.put_object(
                self.bucket, name, BytesIO(payload), len(payload), content_type=content_type
            )
            return f"s3://{self.bucket}/{name}"
        except Exception as exc:
            raise StorageError("Could not store uploaded image in MinIO") from exc
