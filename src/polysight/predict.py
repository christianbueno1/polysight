"""Predicción top-1/top-3 sobre una imagen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from PIL import Image

from .data.dataset import build_transforms
from .model import build_model


@torch.inference_mode()
def predict(checkpoint_path: Path, image_path: Path) -> list[dict[str, float | str]]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    classes: list[str] = checkpoint["classes"]
    config = checkpoint["config"]
    model = build_model(
        len(classes), pretrained=False, dropout=float(config["model"].get("dropout", 0.2))
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device).eval()
    transform = build_transforms(int(config["data"]["image_size"]))["test"]
    with Image.open(image_path) as image:
        tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)
    probabilities = torch.softmax(model(tensor), dim=1)[0]
    k = min(3, len(classes))
    values, indices = probabilities.topk(k)
    return [
        {"class": classes[index], "probability": float(value)}
        for value, index in zip(values.cpu().tolist(), indices.cpu().tolist(), strict=True)
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(predict(args.checkpoint, args.image), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
