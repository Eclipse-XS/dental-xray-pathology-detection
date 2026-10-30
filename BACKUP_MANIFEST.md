# Backup manifest

Status at 2026-10-30: `BACKUP_VERIFIED`. This classification covers GitHub source/history, all four DVC outputs, and the 15-object human-readable Google Drive artifact archive. It does not authorize local deletion; the separate explicit-confirmation safety gate still applies.

## GitHub

- Repository: `https://github.com/Eclipse-XS/dental-xray-pathology-detection`
- Visibility observed during audit: public.
- Default branch: `main`.
- Migration branch: `develop`.
- Restore-tested content commit: `9e66b69ce706b8dd67be971678ed967a2375d7c1`.
- Remote comparison: local `develop`, `origin/develop`, and the GitHub API matched after the restore evidence was committed. The later manifest-only commit does not change any restored payload or DVC pointer.
- Tracked files before the migration commit: 361; the migration commit adds the documentation, dependency manifests, and two MLflow DVC pointers.

Git retains source code, notebooks, configurations, provenance files, experiment definitions, metric tables, figures, deployment code, tests, documentation, and the two DVC pointer files. Git does not retain ignored binary model outputs, the canonical dataset bytes, local environments, caches, secrets, or live MLflow storage.

## DVC remote

- Remote name: `storage`.
- Backend: Google Drive.
- Remote folder ID: `1H8ivmkImy8FmMMC4Xx8bpH6qs8eFDXMG`.
- Objects: canonical DENTEX dataset, selected final FCOS checkpoint, 118-file legacy MLflow directory, and MLflow SQLite database.
- Verification on 2026-10-30: `dvc status -c` reported `Cache and remote 'storage' are in sync` in both the original and clean clone.
- Recovery test: clean clone of `develop` at the verified commit followed by `dvc pull` completed in `E:\dental-xray-restore-test-20261030`.
- Restored dataset: 709 files, 2,893,869,595 bytes. The train, validation, and test annotation SHA-256 values matched `configs/derived_dataset_provenance.yaml`.
- Restored checkpoint SHA-256: `ec4ee94b2bf7afcb77873fe4d26915bec2c7af71f09cd68353beb65561ca783d`.
- Restored MLflow state: 118 files totaling 1,619,148 bytes plus a 4,526,080-byte database. Database SHA-256: `9a1825f66ebccc4a34d205a3ffe0473f98d13b1e5caf9dbf0dbf6c13643f63e0`.

OAuth client configuration and tokens are local secrets. They are not part of the backup manifest and must be recreated by an authorized user during restoration.

## Human-readable large-artifact archive

`artifacts/provenance/artifact_cleanup_report.json` records 15 Google Drive objects totaling 4,149,752,546 bytes. Each record includes logical name, Drive path, file ID, byte size, SHA-256, and prior verification state. On 2026-10-30 every corresponding local file existed and matched its recorded SHA-256:

- final ONNX export and final-evaluation predictions;
- YOLO, SSD, FCOS, Faster R-CNN, and DETR architecture-screening weights;
- refinement checkpoints A4, B3, R1, G2, C1, V3, D4, and E3.

On 2026-10-30 the Google Drive API confirmed that every archived object exists and is not trashed. For all 15 objects, the Drive byte size and MD5 checksum matched the corresponding local file. The local SHA-256 values also matched the committed archive report. The selected final F checkpoint is covered separately by DVC and therefore has two recovery paths.

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
