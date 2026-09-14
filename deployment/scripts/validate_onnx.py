"""Class/IoU-aware real-image parity validation for serving backends."""

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dental_xray_service.inference.onnx_backend import ONNXRuntimeBackend  # noqa: E402
from dental_xray_service.inference.postprocessing import DetectionPostprocessor  # noqa: E402
from dental_xray_service.inference.preprocessing import ImagePreprocessor  # noqa: E402
from dental_xray_service.inference.pytorch_backend import PyTorchBackend  # noqa: E402

SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def box_iou(a: np.ndarray, b: np.ndarray) -> float:
    left, top = np.maximum(a[:2], b[:2])
    right, bottom = np.minimum(a[2:], b[2:])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    union = np.prod(a[2:] - a[:2]) + np.prod(b[2:] - b[:2]) - intersection
    return float(intersection / union) if union > 0 else 0.0


def match_detections(reference, candidate, minimum_iou: float):
    options = []
    for left, (box, label) in enumerate(zip(reference.boxes, reference.labels, strict=True)):
        for right, (other_box, other_label) in enumerate(zip(candidate.boxes, candidate.labels, strict=True)):
            if int(label) == int(other_label):
                options.append((box_iou(box, other_box), left, right))
    matches, used_left, used_right = [], set(), set()
    for iou, left, right in sorted(options, reverse=True):
        if iou >= minimum_iou and left not in used_left and right not in used_right:
            matches.append((left, right, iou))
            used_left.add(left)
            used_right.add(right)
    return (
        matches,
        set(range(len(reference.boxes))) - used_left,
        set(range(len(candidate.boxes))) - used_right,
    )


def resolve_images(inputs: list[Path], sample_size: int) -> list[Path]:
    images = []
    for path in inputs:
        if path.is_dir():
            images.extend(p for p in path.iterdir() if p.suffix.lower() in SUFFIXES)
        else:
            images.append(path)
    return sorted(set(images), key=lambda item: item.name)[:sample_size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--onnx", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("onnx_parity_real_images.json"))
    parser.add_argument("--sample-size", type=int, default=12)
    parser.add_argument("--confidence", type=float, default=0.5)
    parser.add_argument("--minimum-match-iou", type=float, default=0.99)
    parser.add_argument("--max-score-error", type=float, default=1e-3)
    parser.add_argument("--max-box-error", type=float, default=0.1)
    args = parser.parse_args()
    images = resolve_images(args.images, args.sample_size)
    if not images:
        raise FileNotFoundError("No parity images found")
    torch_backend = PyTorchBackend(args.checkpoint, args.metadata, "cpu", 768)
    onnx_backend = ONNXRuntimeBackend(args.onnx, args.metadata, "cpu", 768)
    preprocessor = ImagePreprocessor(20_000_000, 64, 8192, 768)
    postprocessor = DetectionPostprocessor(args.confidence)
    rows, score_errors, box_errors, matched_ious = [], [], [], []
    for image_path in images:
        mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        prepared = preprocessor.prepare(image_path.read_bytes(), mime)
        reference, candidate = torch_backend.predict(prepared), onnx_backend.predict(prepared)
        matches, unmatched_reference, unmatched_candidate = match_detections(
            reference, candidate, args.minimum_match_iou
        )
        for left, right, iou in matches:
            score_errors.append(abs(float(reference.scores[left]) - float(candidate.scores[right])))
            box_errors.extend(np.abs(reference.boxes[left] - candidate.boxes[right]).tolist())
            matched_ious.append(iou)
        restored_reference = postprocessor.apply(reference, prepared)
        restored_candidate = postprocessor.apply(candidate, prepared)
        rows.append(
            {
                "image": image_path.name,
                "width": prepared.original_width,
                "height": prepared.original_height,
                "raw_pytorch": len(reference.boxes),
                "raw_onnx": len(candidate.boxes),
                "matched": len(matches),
                "unmatched_pytorch": len(unmatched_reference),
                "unmatched_onnx": len(unmatched_candidate),
                "post_threshold_pytorch": len(restored_reference),
                "post_threshold_onnx": len(restored_candidate),
            }
        )
    aggregate = {
        "images_evaluated": len(rows),
        "matched_detections": sum(r["matched"] for r in rows),
        "unmatched_pytorch": sum(r["unmatched_pytorch"] for r in rows),
        "unmatched_onnx": sum(r["unmatched_onnx"] for r in rows),
        "label_agreement": 1.0 if matched_ious else None,
        "mean_score_difference": float(np.mean(score_errors)) if score_errors else None,
        "max_score_difference": max(score_errors, default=None),
        "mean_box_coordinate_difference": float(np.mean(box_errors)) if box_errors else None,
        "max_box_coordinate_difference": max(box_errors, default=None),
        "mean_matched_iou": float(np.mean(matched_ious)) if matched_ious else None,
    }
    criteria = {
        "minimum_match_iou": args.minimum_match_iou,
        "maximum_score_error": args.max_score_error,
        "maximum_box_coordinate_error_px": args.max_box_error,
        "unmatched_detections_allowed": 0,
        "post_threshold_count_mismatch_allowed": 0,
    }
    passed = bool(matched_ious) and aggregate["unmatched_pytorch"] == aggregate["unmatched_onnx"] == 0
    passed &= (
        aggregate["max_score_difference"] <= args.max_score_error
        and aggregate["max_box_coordinate_difference"] <= args.max_box_error
    )
    passed &= all(r["post_threshold_pytorch"] == r["post_threshold_onnx"] for r in rows)
    report = {
        "status": "PASS" if passed else "FAIL",
        "acceptance_criteria": criteria,
        "aggregate": aggregate,
        "images": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with args.output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
