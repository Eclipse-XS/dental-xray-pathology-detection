# Architecture

```text
Client -> FastAPI -> DTO/upload validation -> InferenceService
                                             |       |
                                      PyTorchBackend ONNXRuntimeBackend
                                             \       /
                                          DetectionResult
                                                 |
                            PostgreSQL <- Repository -> Object storage
                                                 |
                                             Prometheus -> Grafana

Offline: Airflow -> artifact validation -> ONNX export -> parity -> benchmark -> report
```

This is a modular monolith. Strategy isolates runtimes, the factory selects one runtime, the service owns the use case, repositories isolate persistence, and FastAPI dependencies wire the components. Routes do not know FCOS internals.

The online and offline paths are deliberately separate: FastAPI serves requests; Airflow orchestrates artifact lifecycle jobs.
