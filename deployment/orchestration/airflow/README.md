# Airflow orchestration

Airflow is restricted to offline lifecycle work. `dentex_model_lifecycle` validates the selected artifact, exports ONNX, checks parity, benchmarks it, and publishes a report. It never handles HTTP inference and never trains a model.

Runtime execution is currently blocked: Airflow is not installed in the project environment, and the stock Compose Airflow image does not contain the deployment package, Torch, or ONNX Runtime. The DAG is syntax-checked, but no successful Airflow run is claimed.

The future production-data workflow is intentionally documentation-only: aggregate prediction statistics, check data quality/drift, generate a report, then archive metrics. No drift claims can be made before production data exists.
