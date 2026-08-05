"""Construcción de EfficientNet-B0 para PolySight."""

from __future__ import annotations

from pathlib import Path

import torch
from torch import nn
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


def build_model(
    num_classes: int,
    *,
    pretrained: bool = True,
    weights_path: Path | None = None,
    dropout: float = 0.2,
) -> nn.Module:
    if weights_path:
        model = efficientnet_b0(weights=None)
        state = torch.load(weights_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
    else:
        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = efficientnet_b0(weights=weights)
    in_features = model.classifier[1].in_features
    # Las capas convolucionales están dentro de model.features, 
    # implementadas por torchvision.models.efficientnet_b0. 
    # PolySight únicamente reemplaza la cabeza clasificadora:
    model.classifier = nn.Sequential(
        nn.Dropout(p=dropout), 
        nn.Linear(in_features, num_classes)
    )
    return model


def freeze_backbone(model: nn.Module, frozen: bool) -> None:
    for parameter in model.features.parameters():
        parameter.requires_grad = not frozen
