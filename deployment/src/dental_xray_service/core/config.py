from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DENTEX_", extra="ignore")

    app_name: str = "Dental X-ray Pathology Detection"
    environment: str = "development"
    log_level: str = "INFO"
    backend: Literal["pytorch", "onnx"] = "pytorch"
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[4])
    checkpoint_path: Path | None = None
    model_metadata_path: Path | None = None
    onnx_model_path: Path | None = None
    device: str = "cpu"
    image_size: int = Field(768, ge=64, le=4096)
    confidence_threshold: float = Field(0.5, ge=0, le=1)
    max_upload_bytes: int = Field(15 * 1024 * 1024, gt=0)
    min_image_dimension: int = Field(64, gt=0)
    max_image_dimension: int = Field(8192, gt=0)
    database_url: str = "sqlite:///./deployment_predictions.db"
    persist_predictions: bool = True
    storage_backend: Literal["local", "minio", "none"] = "local"
    storage_path: Path = Path("./runtime/uploads")
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "dentex-predictions"
    prometheus_enabled: bool = True

    @model_validator(mode="after")
    def resolve_artifact_paths(self) -> "Settings":
        root = self.project_root.resolve()
        if self.checkpoint_path is None:
            self.checkpoint_path = root / "artifacts/refinement/fcos/F_final_fcos_tuned/best.pth"
        if self.model_metadata_path is None:
            self.model_metadata_path = root / "artifacts/refinement/fcos/selected_final_model.json"
        if self.onnx_model_path is None:
            self.onnx_model_path = root / "deployment/models/final_fcos_768.onnx"
        if self.min_image_dimension > self.max_image_dimension:
            raise ValueError("min_image_dimension must not exceed max_image_dimension")
        artifact = self.checkpoint_path if self.backend == "pytorch" else self.onnx_model_path
        if not artifact.is_file():
            raise ValueError(f"Configured {self.backend} artifact does not exist: {artifact}")
        if self.device.startswith("cuda"):
            import torch

            if not torch.cuda.is_available():
                raise ValueError("CUDA was requested but torch.cuda.is_available() is false")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
