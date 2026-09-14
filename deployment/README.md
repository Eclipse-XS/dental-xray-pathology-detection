# DENTEX deployment subsystem

Production-like portfolio serving for the already trained and final-test-evaluated `F_final_fcos_tuned` detector. This subsystem performs inference only. It is experimental educational/research software and is not intended for clinical diagnosis or medical decision-making.

## Architecture

The application is a modular monolith: FastAPI validates requests and delegates to `InferenceService`; a backend Strategy runs PyTorch or ONNX Runtime; postprocessing maps the four public classes; a repository persists metadata/detections; image bytes go only to the configured storage adapter. PostgreSQL, Prometheus/Grafana, MinIO, and Airflow are optional infrastructure. See [architecture](docs/architecture.md).

The canonical model is reconstructed from the final notebook recipe:

- experiment: `F_final_fcos_tuned`
- architecture: FCOS ResNet50-FPN
- checkpoint: `artifacts/refinement/fcos/F_final_fcos_tuned/best.pth`
- resolution: 768
- public classes: Impacted, Caries, Periapical Lesion, Deep Caries
- fixed confidence threshold: 0.5, selected before final-test evaluation

## Local setup

Python 3.11 or 3.12 is recommended.

```bash
cd deployment
python -m venv .venv
.venv/Scripts/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env            # use cp on Unix
```

For a host process, set `DENTEX_PROJECT_ROOT` to the repository root and use SQLite or a reachable PostgreSQL URL. Then:

```bash
alembic upgrade head
uvicorn dental_xray_service.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/api/v1/health
curl -F "file=@sample.png" http://127.0.0.1:8000/api/v1/predict
```

The model is loaded, hashed, and warmed once during application lifespan. `/ready` stays unavailable until that completes. Startup rejects missing artifacts, invalid thresholds, and unavailable requested CUDA devices instead of silently falling back.

## Docker

Copy `.env.example` to `.env` and replace development passwords. The model is mounted read-only and is not copied into the image. Dataset and notebooks are excluded.

```bash
docker compose --profile core up --build
docker compose --profile core --profile monitoring up --build
docker compose --profile core --profile storage up --build
docker compose --profile orchestration up airflow
```

Core starts the API and PostgreSQL. Monitoring adds Prometheus on 9090 and Grafana on 3000. Storage adds MinIO on 9000/9001. Airflow is offline orchestration only.

## Backend selection

`DENTEX_BACKEND=pytorch` is the verified default. `DENTEX_DEVICE=cpu` avoids a CUDA requirement. ONNX is opt-in only after successful export and parity validation:

```bash
python -m pip install -e ".[onnx]"
python scripts/export_onnx.py --checkpoint ../artifacts/refinement/fcos/F_final_fcos_tuned/best.pth --metadata ../artifacts/refinement/fcos/selected_final_model.json --output models/final_fcos_768.onnx
python scripts/validate_onnx.py ../data/processed/dentex_diagnosis/images/val --sample-size 12 --checkpoint ../artifacts/refinement/fcos/F_final_fcos_tuned/best.pth --metadata ../artifacts/refinement/fcos/selected_final_model.json --onnx models/final_fcos_768.onnx --output reports/onnx_parity_real_images.json
python scripts/benchmark_backends.py ../data/processed/dentex_diagnosis/images/val/train_0.png --backend onnx --output reports/benchmark_onnx_cpu_canonical.json
```

Exported existence is not proof of parity. Both serving backends now use one canonical aspect-preserving resize and deterministic padding implementation with shared coordinate inversion.

The export is tied to checkpoint SHA256 `ec4ee94b...a783d`. Class/IoU-aware parity passed on 12 real validation images and 574 detections. With the canonical pipeline on the measured Windows host, ONNX CPU model inference averaged 1,078 ms versus 1,490 ms for PyTorch CPU. PyTorch CUDA averaged 92 ms with synchronized timing. ONNX CUDA was unavailable because only CPU and Azure execution providers are installed.

## Executed validation status

- PASS: Ruff and 15 focused tests.
- PASS: ONNX export and 12-image validation parity.
- PASS: Docker CPU image build, clean PostgreSQL migration, API readiness, and real HTTP prediction persistence/retrieval.
- PASS: corrupt, non-image, unsupported, empty, undersized, and oversized upload handling.
- PASS: Prometheus endpoint and structured prediction log fields.
- BLOCKED: Airflow execution; runtime dependencies are not installed in the Airflow environment.
- PASS: dedicated project Git boundary and minimal DVC tracking for the prepared dataset and selected checkpoint; no remote configured.
- BLOCKED: formal MLflow run resolution; the legacy artifact directory lacks `meta.yaml`.

## API and persistence

Endpoints: `GET /api/v1/health`, `GET /api/v1/ready`, `GET /api/v1/model-info`, `POST /api/v1/predict`, `GET /api/v1/predictions/{id}`, `GET /api/v1/predictions`, and `GET /api/v1/metrics`. OpenAPI is at `/docs`.

PostgreSQL contains model versions, request metadata, and normalized detections, never image blobs. Alembic manages its schema. Uploaded images use local storage, MinIO, or no persistence. See [API](docs/api.md), [inference](docs/inference.md), and [database](docs/database.md).

## Observability

Logs are JSON and include a correlation ID, model backend, latency, and detection count; pixels and image data are excluded. The API exports request outcome, inference latency, and class detection counters. Prometheus is preconfigured as a Grafana data source. Create dashboards for rate, error count, p95 inference latency, and class-count trends after real traffic exists.

## ML lifecycle

MLflow remains the experiment system, DVC is designated for data/large artifact pointers, and Airflow handles offline validation/export/parity/benchmark/report orchestration. No historical registry state is fabricated. See [MLOps responsibilities](docs/mlops.md) and [Airflow](orchestration/airflow/README.md).

## Quality checks

```bash
ruff check .
pytest
python -m compileall -q src scripts tests
docker build -t dentex-api .
```

Tests cover preprocessing, postprocessing, backend contract, no-download model construction, API behavior, and repository persistence. They use fake inference and SQLite; CI needs neither a checkpoint nor GPU.
