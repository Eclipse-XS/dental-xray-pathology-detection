# Reproducible environments

## Architecture

The repository has two dependency boundaries:

1. A root Python 3.12 ML environment for training, evaluation, notebooks,
   Ultralytics, DVC, MLflow, ONNX, and experiment analysis.
2. `deployment/`, a separately installable Python 3.11+ service package.

There is no separate YOLO environment. Ultralytics is a direct dependency of
the root ML environment, so it covers the existing YOLO baseline workflow.

Python 3.12 is the canonical root version. It is supported by the pinned ML,
data, DVC, tracking, and notebook packages and avoids relying on the newer
Python 3.13 interpreter from the legacy environment.

## Root ML environment on Windows PowerShell

Run these commands from the repository root. They deliberately create a new
environment; do not reuse `.venv` or `.venv-yolo`.

Before creating a GPU environment while legacy environments are still present,
ensure that the drive has at least 12 GiB free. The CUDA 12.8 PyTorch wheel is
about 2.75 GiB and pip needs additional unpacking space; a complete temporary
validation environment cannot coexist safely with two 10.71-GiB legacy venvs
on a nearly full drive.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements\pytorch-cu128.txt
python -m pip install -e ".[training,notebooks,tracking,dvc,onnx,dev]"
python -m ipykernel install --user --name dental-xray-py312 --display-name "Dental X-ray (Python 3.12)"
```

The canonical GPU combination is PyTorch 2.11.0, torchvision 0.26.0, and
torchaudio 2.11.0 from the CUDA 12.8 index. This is the exact pairing published
by PyTorch for Windows/Linux. A compatible NVIDIA driver is still required;
the CUDA toolkit itself is not required for wheel-based execution.

For CPU-only use, replace the fourth command with:

```powershell
python -m pip install torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cpu
```

## Verification

```powershell
python -c "import torch, torchvision, ultralytics, numpy, pandas, PIL, matplotlib, torchmetrics, pycocotools, mlflow, dvc, transformers, onnx, onnxruntime, sklearn; print(torch.__version__); print(torchvision.__version__); print(torch.cuda.is_available())"
python -c "import torch; assert torch.cuda.is_available(), 'NVIDIA driver/GPU unavailable'; print((torch.ones(1, device='cuda') + 1).item())"
python -m pytest deployment\tests
```

The CUDA tensor command is intentionally expected to fail on a computer with
no CUDA-capable GPU or insufficient driver. The import command must pass in
both CPU and GPU environments.

## DVC

The repository has a configured Google Drive remote. The 2026-10-30 migration
audit verified with `dvc status -c` that the canonical dataset and selected
checkpoint are present and synchronized. Do not run `dvc gc` or delete local
data merely on the strength of this statement: repeat the remote check and a
clean restore test before any destructive cleanup.

After the ML environment is installed, validate only local metadata/state:

```powershell
python -m dvc status
python -m dvc data status --unchanged
```

## Deployment environment

Deployment intentionally remains separate because the Docker image uses
Python 3.11 and CPU PyTorch. From `deployment/`:

```powershell
py -3.11 -m venv .venv-deployment
.\.venv-deployment\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.11.0 torchvision==0.26.0
python -m pip install -e ".[onnx,dev]"
python -m pytest
```

`psycopg[binary]` is correctly declared for PostgreSQL deployment but is not
required for the SQLite test path. `minio` remains optional and is needed only
when object storage is selected. The legacy root environment's Pillow 12.3.0
does not prove a defect in deployment: deployment correctly constrains Pillow
below 12 for its own boundary, and that boundary must be validated separately.
