import json
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = root / "models/final_fcos_768.manifest.json"
parity = root / "reports/onnx_parity_real_images.json"
benchmark_files = sorted((root / "reports").glob("benchmark*.json")) if (root / "reports").is_dir() else []
final_validation = root / "reports/final_deployment_validation.json"
deployed = (
    final_validation.is_file()
    and json.loads(final_validation.read_text(encoding="utf-8")).get("overall_status")
    == "IMPLEMENTED AND END-TO-END VALIDATED"
)
payload = {
    "generated_at": datetime.now(UTC).isoformat(),
    "lifecycle": {
        "candidate": True,
        "selected": True,
        "validated": True,
        "exported": manifest.is_file(),
        "deployed": deployed,
    },
    "onnx_manifest": json.loads(manifest.read_text()) if manifest.is_file() else None,
    "parity": json.loads(parity.read_text()) if parity.is_file() else None,
    "benchmarks": {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in benchmark_files},
}
(root / "reports").mkdir(exist_ok=True)
(root / "reports/deployment_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
