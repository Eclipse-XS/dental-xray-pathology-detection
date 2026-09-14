from pydantic import BaseModel


class ModelInfoResponse(BaseModel):
    experiment_id: str
    model_version: str
    architecture: str
    image_size: int
    class_names: dict[int, str]
    backend: str
    artifact_sha256: str
    runtime: str
    artifact_path: str | None = None
    providers: list[str] | None = None
