from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from polysight.metrics import normalize_confusion_matrix, save_evaluation_artifacts


def test_normalize_confusion_matrix_by_rows_and_preserve_empty_rows() -> None:
    matrix = np.array([[2, 1, 0], [0, 3, 1], [0, 0, 0]])

    normalized = normalize_confusion_matrix(matrix)

    assert normalized[:2].sum(axis=1) == pytest.approx([1.0, 1.0])
    assert normalized[2].tolist() == [0.0, 0.0, 0.0]
    assert normalized[0].tolist() == pytest.approx([2 / 3, 1 / 3, 0])


def test_evaluation_artifacts_include_raw_and_normalized_matrices(tmp_path: Path) -> None:
    classes = ["a", "b", "c"]
    matrix = np.array([[2, 1, 0], [0, 3, 1], [0, 0, 0]])
    summary = {"accuracy": 5 / 7}
    per_class = {
        name: {"precision": 1.0, "recall": 1.0, "f1-score": 1.0, "support": 1.0}
        for name in classes
    }

    paths = save_evaluation_artifacts(tmp_path, summary, per_class, matrix, classes)

    assert {path.name for path in paths} == {
        "metrics.json",
        "per-class-metrics.csv",
        "confusion-matrix.csv",
        "confusion-matrix.png",
        "confusion-matrix-normalized.png",
    }
    assert all(path.is_file() for path in paths)
    with (tmp_path / "confusion-matrix.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    assert rows == [
        ["actual\\predicted", "a", "b", "c"],
        ["a", "2", "1", "0"],
        ["b", "0", "3", "1"],
        ["c", "0", "0", "0"],
    ]


def test_evaluation_artifacts_reject_wrong_matrix_shape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="número de clases"):
        save_evaluation_artifacts(tmp_path, {}, {}, np.zeros((2, 3)), ["a", "b"])
