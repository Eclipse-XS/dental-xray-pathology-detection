# Backup manifest

Status at 2026-10-30: `BACKUP_PARTIAL` until the clean restore test and the new documentation commit are verified remotely. Local deletion is prohibited while this status remains partial.

## GitHub

- Repository: `https://github.com/Eclipse-XS/dental-xray-pathology-detection`
- Visibility observed during audit: public.
- Default branch: `main`.
- Migration branch: `develop`.
- Pre-audit `develop` commit: `f1ec2c23a036a00e537f638c527fbb439e17d28b`.
- Pre-audit remote comparison: local `develop` matched `origin/develop`.
- Tracked files before this documentation update: 361.

Git retains source code, notebooks, configurations, provenance files, experiment definitions, metric tables, figures, deployment code, tests, documentation, and the two DVC pointer files. Git does not retain ignored binary model outputs, the canonical dataset bytes, local environments, caches, secrets, or live MLflow storage.

## DVC remote

- Remote name: `storage`.
- Backend: Google Drive.
- Remote folder ID: `1H8ivmkImy8FmMMC4Xx8bpH6qs8eFDXMG`.
- Objects: canonical DENTEX dataset, selected final FCOS checkpoint, 118-file legacy MLflow directory, and MLflow SQLite database.
- Verification on 2026-10-30: `dvc status -c` reported `Cache and remote 'storage' are in sync` for the repository and for each pointer separately.
- Recovery test: pending completion in `E:\dental-xray-restore-test-20261030` when this file was drafted.

OAuth client configuration and tokens are local secrets. They are not part of the backup manifest and must be recreated by an authorized user during restoration.

## Human-readable large-artifact archive

`artifacts/provenance/artifact_cleanup_report.json` records 15 Google Drive objects totaling 4,149,752,546 bytes. Each record includes logical name, Drive path, file ID, byte size, SHA-256, and prior verification state. On 2026-10-30 every corresponding local file existed and matched its recorded SHA-256:

- final ONNX export and final-evaluation predictions;
- YOLO, SSD, FCOS, Faster R-CNN, and DETR architecture-screening weights;
- refinement checkpoints A4, B3, R1, G2, C1, V3, D4, and E3.

The selected final F checkpoint is covered separately by DVC and therefore has two recovery paths.

## Intentionally excluded local state

| Category | Paths | Reason | Recovery |
|---|---|---|---|
| Secrets | `.dvc/config.local`, `deployment/.env` | Must not be committed or uploaded into a public repository. | Recreate locally from authorized credentials and `.env.example`. |
| IDE state | `.idea/` | User-specific and nonessential. | PyCharm regenerates it. |
| Package output | `*.egg-info/`, Python caches | Derived state. | Reinstall package. |
| Base weights | `yolo26n.pt`, `notebooks/yolo26n.pt` | Downloadable upstream model, not a trained project result. | Redownload through Ultralytics. |
| MLflow live state | `mlruns/`, `artifacts/modeling/mlflow.db` | Binary/runtime content is excluded from Git. | Preserved by `mlruns.dvc` and `artifacts/modeling/mlflow.db.dvc`. |
| DVC cache | `.dvc/cache/` | Local duplicate of verified DVC remote. | `dvc pull`. |

## Safety gate

Do not delete `C:\Users\Eclipse\PycharmProjects\Dental-Xray-Pathology-Detection` unless all of the following are true:

1. this manifest is updated to `BACKUP_VERIFIED` and pushed;
2. the remote branch and commit are fetched and compared;
3. clean Git clone and DVC pull complete in a separate directory;
4. restored hashes and required file counts pass;
5. ignored legacy MLflow state is either classified as disposable or separately archived;
6. no project process is using the directory;
7. the user gives explicit final confirmation for the exact path.
