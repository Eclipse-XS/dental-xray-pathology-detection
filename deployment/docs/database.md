# Database and storage

PostgreSQL stores `model_versions`, `prediction_requests`, and `detections`. Image pixels are not stored in database rows. A prediction references its model version and optional object-storage URI. SQLAlchemy 2.x mappings and the repository layer contain persistence logic; Alembic owns schema migration.

Local development may use SQLite. PostgreSQL is the Compose default. Local filesystem storage is the default image store; MinIO is an optional Compose profile. Set `DENTEX_STORAGE_BACKEND=none` to retain no upload after inference.
