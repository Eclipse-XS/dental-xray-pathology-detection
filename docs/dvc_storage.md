# DVC storage and recovery

## Storage model

GitHub stores the project source code, notebooks, configuration, provenance records, small metadata, and `.dvc` pointer files. It does not store the large binary contents referenced by those pointers.

The default DVC remote, `storage`, uses Google Drive as content-addressed object storage. DVC stores objects under hash-based subdirectories, so the remote does not resemble the human-facing project directory tree. This layout is expected. Do not manually rename, move, or delete objects in the Google Drive DVC folder; use DVC commands to manage and recover them.

## DVC-protected outputs

The remote currently protects:

- the canonical DENTEX dataset referenced by `data/processed/dentex_diagnosis.dvc`;
- the final selected FCOS checkpoint referenced by `artifacts/refinement/fcos/F_final_fcos_tuned/best.pth.dvc`.

The remote does not currently protect:

- `artifacts/modeling/mlflow.db`;
- historical non-final checkpoints;
- `mlruns/`;
- ONNX exports unless they are explicitly added to DVC later.

## Recovery after cloning

A Git clone restores the repository and DVC pointers, but not the referenced dataset or checkpoint bytes. Install DVC with Google Drive support in the project environment, configure local Google OAuth access, and run from the repository root:

```powershell
dvc pull
```

This restores both currently tracked outputs. To restore them individually:

```powershell
dvc pull data/processed/dentex_diagnosis.dvc
dvc pull artifacts/refinement/fcos/F_final_fcos_tuned/best.pth.dvc
```

The remote URL and default remote name are project metadata in `.dvc/config`. OAuth client configuration and tokens are local credentials; they must remain outside tracked files. This repository ignores `.dvc/config.local` for that purpose.

## Synchronization checks

Check the local workspace and compare the local cache with the configured remote using:

```powershell
dvc status
dvc status -c
```

For the two critical outputs specifically:

```powershell
dvc status -c data/processed/dentex_diagnosis.dvc --remote storage
dvc status -c artifacts/refinement/fcos/F_final_fcos_tuned/best.pth.dvc --remote storage
```

The Google Drive folder is a DVC object store, not a manually maintained backup hierarchy. Human-readable names and project structure remain in Git and in the `.dvc` pointer files.
