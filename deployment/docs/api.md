# API

All endpoints are under `/api/v1`.

- `GET /health`: process liveness.
- `GET /ready`: backend readiness.
- `GET /model-info`: loaded model identity and checksum.
- `POST /predict`: multipart image prediction.
- `GET /predictions/{id}`: persisted prediction.
- `GET /predictions?limit=50&before=...`: bounded history.
- `GET /metrics`: Prometheus exposition.

`POST /predict` accepts JPEG, PNG, or WebP subject to byte and dimension limits. Errors do not expose tracebacks. Responses and database records include the experiment, version, backend, runtime, and startup-computed artifact checksum.
