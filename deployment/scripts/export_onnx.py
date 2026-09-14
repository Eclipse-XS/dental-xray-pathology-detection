"""Export the frozen selected FCOS checkpoint. This script never trains or downloads weights."""

import argparse
import json
import sys
from pathlib import Path

import torch

DEPLOYMENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEPLOYMENT_ROOT / "src"))

from dental_xray_service.models.fcos import build_final_fcos  # noqa: E402
from dental_xray_service.models.metadata import sha256_file  # noqa: E402


class FCOSExportWrapper(torch.nn.Module):
    """Stable single-image serving contract: boxes, scores, labels, count."""

    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, image):
        output = self.model([image])[0]
        return output["boxes"], output["scores"], output["labels"], torch.tensor(output["scores"].shape[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-size", type=int, default=768)
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()
    for path in (args.checkpoint, args.metadata):
        if not path.is_file():
            raise FileNotFoundError(path)
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    if metadata.get("selected_final_experiment_id") != "F_final_fcos_tuned":
        raise RuntimeError("Refusing to export a model other than F_final_fcos_tuned")
    model = build_final_fcos(args.image_size)
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(payload["model_state_dict"], strict=True)
    wrapper = FCOSExportWrapper(model.eval())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample = torch.zeros((3, args.image_size, args.image_size), dtype=torch.float32)
    torch.onnx.export(
        wrapper,
        (sample,),
        args.output,
        opset_version=args.opset,
        input_names=["image"],
        output_names=["boxes", "scores", "labels", "num_detections"],
        dynamic_axes={"boxes": {0: "detections"}, "scores": {0: "detections"}, "labels": {0: "detections"}},
        dynamo=False,
    )
    manifest = {
        "status": "exported_unvalidated",
        "experiment_id": "F_final_fcos_tuned",
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha256_file(args.checkpoint),
        "onnx_path": str(args.output.resolve()),
        "onnx_sha256": sha256_file(args.output),
        "input": {
            "name": "image",
            "shape": [3, args.image_size, args.image_size],
            "dtype": "float32",
            "range": [0, 1],
        },
        "outputs": ["boxes", "scores", "labels", "num_detections"],
        "opset": args.opset,
    }
    args.output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
