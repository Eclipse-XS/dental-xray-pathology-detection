from functools import partial

import torch.nn as nn
from torchvision.models.detection import fcos_resnet50_fpn
from torchvision.models.detection.fcos import FCOSClassificationHead


def build_final_fcos(image_size: int = 768):
    """Reconstruct the exact final-evaluation architecture without downloads."""
    model = fcos_resnet50_fpn(
        weights=None,
        weights_backbone=None,
        min_size=image_size,
        max_size=image_size,
    )
    model.head.classification_head = FCOSClassificationHead(
        model.backbone.out_channels,
        model.anchor_generator.num_anchors_per_location()[0],
        5,
        norm_layer=partial(nn.GroupNorm, 32),
    )
    return model
