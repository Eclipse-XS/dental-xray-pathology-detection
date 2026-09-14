"""Offline selected-model deployment validation. No online inference and no training."""
from datetime import datetime
import os
import subprocess
from pathlib import Path

from airflow.decorators import dag, task

PROJECT = Path(os.environ.get("AIRFLOW_PROJ_DIR", "/project"))
DEPLOY = PROJECT / "deployment"
PYTHON = "python"


def run_script(script: str, *args: str) -> None:
    subprocess.run([PYTHON, str(DEPLOY / "scripts" / script), *args], check=True, cwd=DEPLOY)


@dag(schedule=None, start_date=datetime(2025, 1, 1), catchup=False, tags=["dentex", "deployment"])
def dentex_model_lifecycle():
    @task
    def validate_artifacts():
        run_script("validate_artifacts.py")

    @task
    def verify_selected_model():
        run_script("verify_artifacts.py")

    @task
    def export_onnx():
        run_script("export_onnx.py", "--checkpoint", str(PROJECT / "artifacts/refinement/fcos/F_final_fcos_tuned/best.pth"),
                   "--metadata", str(PROJECT / "artifacts/refinement/fcos/selected_final_model.json"),
                   "--output", str(DEPLOY / "models/final_fcos_768.onnx"))

    @task
    def validate_onnx_parity():
        run_script("validate_onnx.py", str(PROJECT / "data/processed/dentex_diagnosis/images/val"), "--sample-size", "12",
                   "--checkpoint", str(PROJECT / "artifacts/refinement/fcos/F_final_fcos_tuned/best.pth"),
                   "--metadata", str(PROJECT / "artifacts/refinement/fcos/selected_final_model.json"),
                   "--onnx", str(DEPLOY / "models/final_fcos_768.onnx"), "--output", str(DEPLOY / "reports/onnx_parity_real_images.json"))

    @task
    def benchmark_model():
        run_script("benchmark_backends.py", str(PROJECT / "data/processed/dentex_diagnosis/images/val/train_0.png"),
                   "--backend", "onnx", "--output", str(DEPLOY / "reports/benchmark.json"))

    @task
    def publish_deployment_report():
        run_script("deployment_report.py")

    validate_artifacts() >> verify_selected_model() >> export_onnx() >> validate_onnx_parity() >> benchmark_model() >> publish_deployment_report()


dentex_model_lifecycle()
