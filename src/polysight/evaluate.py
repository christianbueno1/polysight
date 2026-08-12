"""Evaluación de checkpoints PolySight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from .config import load_config
from .data.dataset import build_dataloaders
from .metrics import calculate_metrics, save_evaluation_artifacts
from .model import build_model


def load_classes(manifest: Path) -> list[str]:
    class_path = manifest.parent / "classes.json"
    mapping = json.loads(class_path.read_text(encoding="utf-8"))
    return [name for name, _ in sorted(mapping.items(), key=lambda item: item[1])]


@torch.inference_mode()
def collect_predictions(
    model: nn.Module, loader: DataLoader, device: torch.device
) -> tuple[np.ndarray, np.ndarray]:
    model.eval()
    targets: list[np.ndarray] = []
    probabilities: list[np.ndarray] = []
    for images, labels, _ in loader:
        logits = model(images.to(device, non_blocking=True))
        probabilities.append(torch.softmax(logits, dim=1).cpu().numpy())
        targets.append(labels.numpy())
    return np.concatenate(targets), np.concatenate(probabilities)


def evaluate_checkpoint(
    config_path: Path, checkpoint_path: Path, split: str, output_dir: Path
) -> dict[str, float]:
    config = load_config(config_path)
    manifest = Path(config.data.manifest)
    classes = load_classes(manifest)
    loaders = build_dataloaders(
        Path(config.data.data_dir),
        manifest,
        config.data.image_size,
        config.data.batch_size,
        config.data.num_workers,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(len(classes), pretrained=False, dropout=config.model.dropout)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    targets, probabilities = collect_predictions(model, loaders[split], device)
    summary, per_class, matrix = calculate_metrics(targets, probabilities, classes)
    save_evaluation_artifacts(output_dir, summary, per_class, matrix, classes)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--split", choices=("validation", "test"), default="test")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/evaluation"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metrics = evaluate_checkpoint(args.config, args.checkpoint, args.split, args.output_dir)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
