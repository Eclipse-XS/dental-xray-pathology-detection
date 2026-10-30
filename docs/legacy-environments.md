# Legacy environment recovery snapshots

These are forensic snapshots of the two pre-existing virtual environments.
They are not the canonical dependency definition: use `pyproject.toml` and
`requirements/pytorch-cu128.txt` for the future root environment. The files
`requirements-legacy-venv.txt` and `requirements-legacy-yolo.txt` record the
actual legacy state only.

Snapshot generation command:

```powershell
.\.venv\Scripts\python.exe -m pip freeze
.\.venv-yolo\Scripts\python.exe -m pip freeze
```

## `.venv`

| Field | Recorded value |
|---|---|
| Python | CPython 3.13.5, 64-bit |
| Python executable | `C:\Users\Eclipse\PycharmProjects\Dental-Xray-Pathology-Detection\.venv\Scripts\python.exe` |
| pip | 25.1.1 |
| Package count | 268 |
| PyTorch | `2.11.0+cu128` |
| torchvision | `0.26.0+cu128` |
| torchaudio | `2.11.0+cu128` |
| Ultralytics | `8.4.143` |
| PyTorch CUDA build / `torch.version.cuda` | 12.8 |
| `torch.cuda.is_available()` | `True` |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| Platform | Windows-11-10.0.26200-SP0 |
| Snapshot | `requirements-legacy-venv.txt` |

Recommended restoration sequence, without executing it now:

```powershell
py -3.13 -m venv .venv-restored
.\.venv-restored\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cu128 torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0
python -m pip install -r requirements-legacy-venv.txt
```

The CUDA 12.8 index and torch/torchvision/torchaudio version trio are the
official PyTorch installation combination. A compatible NVIDIA driver is still
required for CUDA availability.

## `.venv-yolo`

| Field | Recorded value |
|---|---|
| Python | CPython 3.12.6, 64-bit |
| Python executable | `C:\Users\Eclipse\PycharmProjects\Dental-Xray-Pathology-Detection\.venv-yolo\Scripts\python.exe` |
| pip | 26.2.1 |
| Package count | 76 |
| PyTorch | `2.14.0+cu126` |
| torchvision | `0.29.0+cu126` |
| torchaudio | **Not installed** |
| Ultralytics | `8.4.143` |
| PyTorch CUDA build / `torch.version.cuda` | 12.6 |
| `torch.cuda.is_available()` | `True` |
| GPU | NVIDIA GeForce RTX 3050 Laptop GPU |
| Platform | Windows-11-10.0.26200-SP0 |
| Snapshot | `requirements-legacy-yolo.txt` |

Recommended restoration sequence, without executing it now:

```powershell
py -3.12 -m venv .venv-yolo-restored
.\.venv-yolo-restored\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://download.pytorch.org/whl/cu126 torch==2.14.0 torchvision==0.29.0
python -m pip install -r requirements-legacy-yolo.txt
```

The `+cu126` suffix identifies the required CUDA 12.6 PyTorch wheel index.
This command is a reconstruction instruction inferred from the installed wheel
build tags; availability must be checked against the PyTorch index at restore
time. Do not add torchaudio: it was absent from this legacy environment.

## Nonstandard requirement entries

Both snapshots were checked for editable installs (`-e`), `file://` entries,
`git+` URLs, local paths, and direct HTTP(S) URLs. None were found. Every line
is a normal pinned `distribution==version` entry, so there are no local-source
dependencies that would become unrecoverable when the virtual environments are
removed.

## Restoration limits

`pip freeze` preserves installed distribution versions but not wheel hashes,
the original pip download cache, the NVIDIA driver version, or package indexes
other than the PyTorch CUDA source reconstructed above. The snapshots are
therefore emergency recovery records, not cryptographic lock files. Python
3.13 support and future availability of the recorded package wheels may also
change; restore them before deleting the corresponding environment if exact
legacy recovery is required.
