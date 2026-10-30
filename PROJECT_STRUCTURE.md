# Project structure and storage classification

Audit date: 2026-10-30. Audit root: `C:\Users\Eclipse\PycharmProjects\Dental-Xray-Pathology-Detection`.

| Path | Class | Audit size | Purpose and retention rule |
|---|---|---:|---|
| `.git/` | `REGENERABLE` | 0.0523 GiB | Local Git object database; recover from GitHub after remote verification. |
| `.dvc/` | `CRITICAL_DATA` / `CACHE` / `SENSITIVE` | 3.0525 GiB | Tracked remote configuration, local content cache, temporary locks, and untracked OAuth settings. Preserve until DVC restore is verified. Never commit `config.local`. |
| `.github/` | `SOURCE_CODE` | <0.001 GiB | Repository automation metadata. |
| `.idea/` | `REGENERABLE` | <0.001 GiB | PyCharm user state; ignored and not required for reproduction. |
| `archive/` | `SOURCE_CODE` | 0.0006 GiB | Legacy experiment notebook retained for provenance. |
| `artifacts/` | `EXPERIMENT_RESULT` / `MODEL_ARTIFACT` | 4.1302 GiB | Metrics, histories, reports and figures are tracked; ignored checkpoints and predictions are externally archived. The final checkpoint is also DVC-managed. |
| `configs/` | `CRITICAL_DATA` | <0.001 GiB | Dataset provenance, class mapping, source hashes and filename manifest. |
| `data/` | `CRITICAL_DATA` | 2.6951 GiB | Canonical 705-image/3,529-annotation DENTEX split. Managed by DVC. |
| `deployment/` | `SOURCE_CODE` / `MODEL_ARTIFACT` / `SENSITIVE` | 0.1201 GiB | FastAPI service and validation reports are tracked. ONNX is archived externally. `.env` is local and ignored. |
| `docs/` | `SOURCE_CODE` | <0.001 GiB | Environment and DVC recovery documentation. |
| `mlruns/` | `EXPERIMENT_RESULT` | 0.0015 GiB | Ignored legacy MLflow state, preserved through `mlruns.dvc`. |
| `notebooks/` | `SOURCE_CODE` / `EXPERIMENT_RESULT` | 0.0272 GiB | Executable research narrative with saved outputs. |
| `requirements/`, `pyproject.toml`, legacy requirement files | `SOURCE_CODE` | <0.001 GiB | Reproducible dependency definitions and legacy environment snapshots. |
| `scripts/` | `SOURCE_CODE` | <0.001 GiB | MLflow metadata normalization utility. |
| `dental_xray_pathology_detection.egg-info/` | `REGENERABLE` | <0.001 GiB | Local packaging output; ignored. |
| `yolo26n.pt`, `notebooks/yolo26n.pt` | `MODEL_ARTIFACT` / `REGENERABLE` | 0.0103 GiB combined | Downloadable Ultralytics base weights, ignored. They are not trained project outputs. |

Total audit: 3,054 files, 10,828,370,994 bytes (10.085 GiB). The dominant file types are PyTorch checkpoints (4.232 GB), DVC hash objects with no extension (3.334 GB), PNG images (2.914 GB), SafeTensors (166 MB), and ONNX (129 MB).

## Critical boundaries

- GitHub is the authoritative store for source, notebooks, documentation, provenance, small reports, and DVC pointer files.
- Google Drive DVC remote `storage` is the authoritative content-addressed store for the canonical dataset, selected final checkpoint, MLflow directory, and MLflow SQLite database.
- The human-readable Google Drive archive described in `artifacts/provenance/artifact_cleanup_report.json` stores 15 large binary outputs by logical name and SHA-256.
- Local `.dvc/cache` duplicates the DVC-managed objects and is regenerable only after remote verification.
- `deployment/.env` and `.dvc/config.local` are sensitive local configuration. They are excluded from all backups by design; only non-secret examples and setup instructions are retained.

No symlinks, junctions, or nested Git repositories were found during the audit.
