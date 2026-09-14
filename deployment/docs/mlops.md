# MLOps responsibilities

- Git: source, configuration, documentation, small metadata, DVC pointer files.
- DVC: prepared splits and large artifacts such as checkpoints/exports.
- MLflow: experiment runs, parameters, metrics, and modeling lineage.
- Airflow: offline deployment-artifact validation and reporting.

The existing MLflow run `5b2630950f384adeb9c68bacc44764bb` is referenced read-only by `scripts/mlflow_lifecycle.py`. The lifecycle is candidate -> selected -> validated -> exported -> deployed. Only the first three states are established by current evidence. No registry entry is fabricated.

The existing project uses MLflow's legacy filesystem store. The bridge enables MLflow 3's read-only compatibility flag locally; it does not migrate or mutate the store. A later controlled migration to a database tracking backend should use MLflow's official migration command after a backup.

The project now has its own Git boundary and a minimal initialized DVC repository. DVC tracks only `data/processed/dentex_diagnosis` and `artifacts/refinement/fcos/F_final_fcos_tuned/best.pth`. The 705 images, three annotation files, and checkpoint remain present; the checkpoint SHA256 is unchanged. No DVC remote or credentials were invented. The included lifecycle stage verifies immutable selected artifacts; notebook cells were not converted into stages.
