# Inference contract

The selected model is `F_final_fcos_tuned`, FCOS ResNet50-FPN, best epoch 17. The PyTorch builder exactly reconstructs the final-evaluation architecture and loads `model_state_dict` strictly. It never requests pretrained weights.

Input decoding follows final evaluation: strict image decode, RGB conversion, aspect-ratio-preserving resize with longest side 768, and top-left placement on a 768-square canvas. Padding uses the exact ImageNet RGB mean, becoming zero after the model's internal normalization and matching torchvision's normalized batch-padding semantics. Both backends receive the same CHW float32 `[0, 1]` tensor. No augmentation is used. One stored spatial transform restores boxes to source coordinates before clipping. Model labels 1–4 become public class IDs 0–3.

ONNX has a fixed `3x768x768` float32 contract and stable outputs: `boxes`, `scores`, `labels`, `num_detections`. Export and coordinate inversion are backend-independent. Twelve real validation images passed class/IoU-aware parity. The canonical padding adds more background than torchvision's minimal divisible-by-32 batch padding, so this is a deliberate production serving contract shared by both runtimes, not a claim that the deployment input tensor is byte-identical to every notebook-internal intermediate.
