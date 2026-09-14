"""Benchmark warmed pure-backend and end-to-end latency without training."""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

DEPLOYMENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_ROOT / "src"))

from dental_xray_service.core.config import Settings  # noqa: E402
from dental_xray_service.inference.factory import create_backend  # noqa: E402
from dental_xray_service.inference.postprocessing import DetectionPostprocessor  # noqa: E402
from dental_xray_service.inference.preprocessing import ImagePreprocessor  # noqa: E402


def summarize(values: list[float]) -> dict:
    ordered = sorted(values)
    p95 = ordered[min(len(ordered) - 1, int(np.ceil(0.95 * len(ordered))) - 1)]
    mean = statistics.mean(values)
    return {"mean_ms": mean, "median_ms": statistics.median(values), "p95_ms": p95, "fps": 1000 / mean}


def synchronize(device: str) -> None:
    if device.startswith("cuda"):
        import torch

        torch.cuda.synchronize()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--backend", choices=("pytorch", "onnx"), default="pytorch")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("benchmark.json"))
    args = parser.parse_args()
    settings = Settings(backend=args.backend, device=args.device)
    backend = create_backend(settings)
    mime = "image/png" if args.image.suffix.lower() == ".png" else "image/jpeg"
    payload = args.image.read_bytes()
    preprocessor = ImagePreprocessor(
        settings.max_upload_bytes,
        settings.min_image_dimension,
        settings.max_image_dimension,
        settings.image_size,
    )
    postprocessor = DetectionPostprocessor(settings.confidence_threshold)
    prepared = preprocessor.prepare(payload, mime)
    for _ in range(args.warmup):
        backend.predict(prepared)
    preprocessing, inference, postprocessing, end_to_end = [], [], [], []
    for _ in range(args.iterations):
        start = time.perf_counter()
        current = preprocessor.prepare(payload, mime)
        preprocessing.append((time.perf_counter() - start) * 1000)
        synchronize(args.device)
        start = time.perf_counter()
        raw = backend.predict(current)
        synchronize(args.device)
        inference.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        postprocessor.apply(raw, current)
        postprocessing.append((time.perf_counter() - start) * 1000)
        synchronize(args.device)
        start = time.perf_counter()
        current = preprocessor.prepare(payload, mime)
        raw = backend.predict(current)
        postprocessor.apply(raw, current)
        synchronize(args.device)
        end_to_end.append((time.perf_counter() - start) * 1000)
    report = {
        "backend": backend.metadata(),
        "iterations": args.iterations,
        "warmup_iterations": args.warmup,
        "execution_provider": backend.metadata().get("providers", [args.device]),
        "threading": {"onnx_intra_op_threads": "runtime_default", "onnx_inter_op_threads": "runtime_default"},
        "preprocessing": summarize(preprocessing),
        "model_inference": summarize(inference),
        "postprocessing": summarize(postprocessing),
        "end_to_end": summarize(end_to_end),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
