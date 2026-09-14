import hashlib
import json
from pathlib import Path
from typing import Any

from dental_xray_service.core.constants import CLASS_NAMES, EXPERIMENT_ID, MODEL_ARCHITECTURE


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_model_identity(metadata_path: Path, artifact_path: Path, backend: str) -> dict[str, Any]:
    source = json.loads(metadata_path.read_text(encoding="utf-8"))
    selected = source.get("selected_final_experiment_id")
    if selected != EXPERIMENT_ID:
        raise ValueError(f"Expected selected experiment {EXPERIMENT_ID}, found {selected}")
    return {
        "experiment_id": selected,
        "model_version": f"{selected}-epoch-{source['best_epoch']}",
        "architecture": MODEL_ARCHITECTURE,
        "image_size": int(source["image_size"]),
        "class_names": CLASS_NAMES,
        "backend": backend,
        "artifact_path": str(artifact_path),
        "artifact_sha256": sha256_file(artifact_path),
    }
