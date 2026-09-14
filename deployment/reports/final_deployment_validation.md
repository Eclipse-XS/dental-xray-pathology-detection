# Final deployment validation

Overall status: **IMPLEMENTED AND END-TO-END VALIDATED** for the core FastAPI, frozen-model, storage, and PostgreSQL serving path.

| Component | Status | Evidence |
|---|---|---|
| Frozen model identity | PASS | `F_final_fcos_tuned`, epoch 17, checkpoint SHA256 `ec4ee94b...a783d` |
| Canonical preprocessing | PASS | Shared aspect-preserving 768 letterbox and inverse-coordinate tests |
| ONNX export | PASS | Fixed `3x768x768` contract; SHA256 `f7ec4a2b...6299b` |
| Real-image parity | PASS | 12 validation images; 574 matches; zero unmatched; mean IoU 0.99999895 |
| CPU benchmark | PASS | PyTorch 1490 ms; ONNX 1078 ms model mean |
| CUDA benchmark | PASS | PyTorch 92.45 ms model mean with synchronization |
| ONNX CUDA | BLOCKED | CUDAExecutionProvider unavailable |
| Docker build | PASS | CPU-only image built |
| Docker core runtime | PASS | API and healthy PostgreSQL running |
| Clean migration | PASS | Alembic upgraded empty PostgreSQL to head |
| Real HTTP prediction | PASS | Prediction `cd61238e-b7c3-4803-adfb-9c89b0c09d78`, six detections |
| PostgreSQL persistence/retrieval | PASS | Request, detections, model FK, detail and list endpoints verified |
| Failure paths | PASS | Six invalid upload categories returned controlled 422 responses |
| Prometheus/logging | PASS | Metrics exposed; traceable structured prediction log verified |
| Ruff | PASS | Clean |
| Pytest | PASS | 15 tests |
| Airflow run | BLOCKED | Runtime dependencies unavailable; DAG static validation passed |
| DVC initialization | PASS | Dedicated project Git boundary; prepared dataset and selected checkpoint tracked; no remote configured |
| MLflow formal run | BLOCKED | Existing run artifact directory lacks `meta.yaml` |

The canonical input path strictly decodes RGB, preserves aspect ratio while resizing the longest side to 768, places the image at the top-left of a 768-square ImageNet-mean canvas, and stores the scale/padding transform. Both runtimes consume that tensor. Postprocessing performs one inverse transform and clips boxes to source dimensions.

The existing ONNX graph was not overwritten because its fixed tensor contract did not change. The new external canonical preprocessing passed stronger parity against it.

No sensitive image content is present in this report.

- Model retraining performed: NO
- Hyperparameter tuning performed: NO
- Test-based model selection performed: NO
