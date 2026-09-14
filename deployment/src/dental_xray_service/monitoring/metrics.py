from prometheus_client import Counter, Histogram

PREDICTIONS = Counter("dentex_predictions_total", "Completed prediction requests", ["backend", "status"])
DETECTIONS = Counter("dentex_detections_total", "Returned detections", ["class_name"])
INFERENCE_LATENCY = Histogram(
    "dentex_inference_seconds",
    "Inference latency in seconds",
    ["backend"],
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
