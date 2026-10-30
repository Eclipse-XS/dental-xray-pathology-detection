# Setup and reproduction

## Prerequisites

- Windows or Linux with Python 3.12 for the research workspace.
- Git.
- DVC with Google Drive support.
- Access to the project Google Drive DVC remote.
- For the pinned CUDA environment: an NVIDIA driver compatible with CUDA 12.8 wheels. CPU-only installation is possible but training will be materially slower.

## Environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements\pytorch-cu128.txt
python -m pip install -e ".[training,notebooks,tracking,dvc,onnx,dev]"
```

For CPU-only PyTorch, replace the CUDA requirements command with the CPU index command documented in `docs/environment.md`.

## Restore large data

The repository does not contain large binary contents. Configure OAuth values only in `.dvc/config.local`, then run:

```powershell
dvc status -c --remote storage
dvc pull --remote storage
```

Expected DVC outputs:

- `data/processed/dentex_diagnosis`: 709 files, 2,893,869,595 bytes, DVC directory hash `69add7b4710ae4ee282d18c5b02f155e.dir`.
- `artifacts/refinement/fcos/F_final_fcos_tuned/best.pth`: 383,672,722 bytes, DVC MD5 `23e6ac9d72687f1c99b73c671a527a54`, SHA-256 `ec4ee94b2bf7afcb77873fe4d26915bec2c7af71f09cd68353beb65561ca783d`.
- `mlruns`: 118 files, 1,619,148 bytes, DVC directory hash `b6b96145e289edde3a8dffa5e6a31a42.dir`.
- `artifacts/modeling/mlflow.db`: 4,526,080 bytes, DVC MD5 `13ceca96c4d25bcd0bbab1a617836671`.

The remaining archived checkpoints and ONNX export are not required to rerun the notebook workflow. Restore them from the logical paths and file IDs recorded in `artifacts/provenance/artifact_cleanup_report.json` when historical binary parity is required.

## Validate the restored state

```powershell
git status --short --branch
dvc status
dvc status -c --remote storage
python -m compileall -q deployment\src deployment\scripts
python -m pytest deployment\tests
```

For content validation:

```powershell
(Get-FileHash -Algorithm SHA256 artifacts\refinement\fcos\F_final_fcos_tuned\best.pth).Hash
(Get-FileHash -Algorithm SHA256 deployment\models\final_fcos_768.onnx).Hash
```

The ONNX checksum should be `f7ec4a2bdc7b2aaaa1b6e5104374f8ac9c19a94428b4d366722b4bc8a362699b` if that optional archived export has been restored.

## Reproduce the research workflow

Run notebooks `00` through `08` in order. Use the saved split seed `42` and the canonical dataset. The prepared split is 493 training, 106 validation, and 106 test images. Do not use the test split for model selection. Existing experiment metrics are evidence of prior runs, not a guarantee that retraining on different hardware or package versions will be bit-for-bit identical.

The deployment subsystem has its own package boundary and instructions in `deployment/README.md`.

## Source reconstruction fallback

If DVC access is unavailable, the raw source provenance identifies the external DENTEX Challenge 2023 dataset, selected source path, filenames, and hashes. This is a fallback reconstruction route, not a verified substitute for `dvc pull`, because the external dataset revision is not pinned.
