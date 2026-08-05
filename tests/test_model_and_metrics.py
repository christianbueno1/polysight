from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("torchvision")

from polysight.data.dataset import HyperKvasirDataset, build_transforms
from polysight.metrics import calculate_metrics
from polysight.model import build_model
from polysight.train import class_weights


def test_efficientnet_output_shape_without_pretrained_download() -> None:
    model = build_model(16, pretrained=False)
    model.eval()
    with torch.inference_mode():
        output = model(torch.zeros(1, 3, 224, 224))
    assert output.shape == (1, 16)


def test_weighted_loss_weights_are_normalized(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["relative_path", "label", "class_index", "split", "sha256"],
        )
        writer.writeheader()
        for index in range(6):
            writer.writerow(
                {
                    "relative_path": f"{index}.jpg",
                    "label": "a" if index < 4 else "b",
                    "class_index": 0 if index < 4 else 1,
                    "split": "train",
                    "sha256": str(index),
                }
            )
    dataset = HyperKvasirDataset(tmp_path, manifest, "train", build_transforms(224)["train"])
    weights = class_weights(dataset, 2)
    assert weights.mean().item() == pytest.approx(1.0)
    assert weights[1] > weights[0]


def test_metrics_include_macro_and_top3() -> None:
    targets = np.array([0, 1, 2, 2])
    probabilities = np.array(
        [[0.8, 0.1, 0.1], [0.1, 0.7, 0.2], [0.1, 0.2, 0.7], [0.2, 0.5, 0.3]]
    )
    summary, per_class, matrix = calculate_metrics(targets, probabilities, ["a", "b", "c"])
    assert "macro_f1" in summary
    assert summary["top_3_accuracy"] == 1.0
    assert set(per_class) == {"a", "b", "c"}
    assert matrix.shape == (3, 3)
