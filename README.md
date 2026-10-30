# Dental X-ray Pathology Detection

Research and deployment workspace for object detection on the DENTEX Challenge 2023 dental X-ray dataset. The public classes are `Impacted`, `Caries`, `Periapical Lesion`, and `Deep Caries`. This is educational/research software, not a clinical diagnostic system.

The repository records the complete notebook workflow, experiment metadata, evaluation outputs, deployment service, provenance, and DVC pointers. Large datasets and model binaries are intentionally stored outside Git.

## Workflow

Run the notebooks in numeric order:

1. `00_prepare_dataset.ipynb` builds the canonical COCO-style split.
2. `01_eda.ipynb` explores the prepared data.
3. `02_preprocessing.ipynb` validates preprocessing and derives the YOLO representation.
4. `03_baseline.ipynb` trains the YOLO baseline.
5. `04_train_models.ipynb` compares DETR, SSD, FCOS, and Faster R-CNN.
6. `05_model_comparison.ipynb` selects the refinement target.
7. `06_fcos_refinement.ipynb` records the FCOS refinement grid.
8. `07_final_evaluation.ipynb` performs the held-out evaluation.
9. `08_error_analysis.ipynb` analyzes failure modes.

The selected model is `F_final_fcos_tuned`, FCOS with a ResNet50-FPN backbone at 768-pixel input resolution. Recorded metrics are retained under `artifacts/`; this README does not restate or reinterpret them.

## Restore

Clone the repository, check out the intended branch, create the root environment, configure Google OAuth locally, and pull DVC data:

```powershell
git clone https://github.com/Eclipse-XS/dental-xray-pathology-detection.git
cd dental-xray-pathology-detection
git checkout develop
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements\pytorch-cu128.txt
python -m pip install -e ".[training,notebooks,tracking,dvc,onnx,dev]"
dvc pull --remote storage
```

See `SETUP_AND_REPRODUCTION.md` for verification and `BACKUP_MANIFEST.md` for the backup boundary. OAuth credentials belong in `.dvc/config.local`; they must never be committed.

## Repository map

- `notebooks/`: the research workflow.
- `artifacts/`: tracked metrics, reports, figures, and DVC metadata; large binary outputs are ignored.
- `data/processed/dentex_diagnosis.dvc`: pointer to the canonical dataset.
- `mlruns.dvc` and `artifacts/modeling/mlflow.db.dvc`: pointers to retained legacy MLflow state.
- `configs/`: source and derived-data provenance.
- `deployment/`: FastAPI service, tests, container configuration, monitoring, database migrations, and model validation scripts.
- `docs/`: environment and storage documentation.
- `scripts/`: maintenance and normalization utilities.

Detailed classification is in `PROJECT_STRUCTURE.md`.
