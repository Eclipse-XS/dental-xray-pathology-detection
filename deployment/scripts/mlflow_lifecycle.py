"""Read-only bridge from the existing MLflow experiment run to deployment state."""

import argparse
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

import mlflow
from mlflow.exceptions import MlflowException


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-uri", required=True)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    selected = json.loads(args.metadata.read_text(encoding="utf-8"))
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    run_id = metrics.get("mlflow_run_id")
    if not run_id:
        raise RuntimeError("Selected experiment has no recorded MLflow run ID")
    # MLflow 3 keeps legacy file stores read-only behind an explicit compatibility flag.
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    mlflow.set_tracking_uri(args.tracking_uri)
    try:
        run = mlflow.get_run(run_id)
        mlflow_status = run.info.status
        source = "existing_mlflow_run"
        note = "Existing run read successfully; no registry state was created or fabricated."
    except MlflowException as exc:
        parsed = urlparse(args.tracking_uri)
        tracking_root = Path(unquote(parsed.path.lstrip("/"))) if parsed.scheme == "file" else None
        run_artifacts = tracking_root / "1" / run_id / "artifacts" if tracking_root else None
        if not run_artifacts or not run_artifacts.is_dir():
            raise
        mlflow_status = "RUN_METADATA_MISSING"
        source = "existing_mlflow_artifact_directory"
        note = (
            "Artifacts exist for the recorded run ID, but meta.yaml is absent, so MLflow cannot "
            f"resolve the run ({exc}). No registry or run state was fabricated."
        )
    report = {
        "run_id": run_id,
        "experiment_id": selected["selected_final_experiment_id"],
        "mlflow_status": mlflow_status,
        "lifecycle": {
            "candidate": True,
            "selected": True,
            "validated": True,
            "exported": False,
            "deployed": False,
        },
        "source": source,
        "note": note,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
