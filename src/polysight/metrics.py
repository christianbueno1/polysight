"""Métricas y artefactos de evaluación multiclase."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    top_k_accuracy_score,
)


def calculate_metrics(
    targets: np.ndarray, probabilities: np.ndarray, class_names: list[str]
) -> tuple[dict[str, float], dict[str, dict[str, float]], np.ndarray]:
    predictions = probabilities.argmax(axis=1)
    labels = np.arange(len(class_names))
    top_k = min(3, len(class_names))
    summary = {
        "accuracy": float(accuracy_score(targets, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(targets, predictions)),
        "macro_f1": float(f1_score(targets, predictions, average="macro", zero_division=0)),
        "weighted_f1": float(
            f1_score(targets, predictions, average="weighted", zero_division=0)
        ),
        f"top_{top_k}_accuracy": float(
            top_k_accuracy_score(targets, probabilities, k=top_k, labels=labels)
        ),
    }
    report = classification_report(
        targets,
        predictions,
        labels=labels,
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    per_class = {name: report[name] for name in class_names}
    matrix = confusion_matrix(targets, predictions, labels=labels)
    return summary, per_class, matrix


def save_evaluation_artifacts(
    output_dir: Path,
    summary: dict[str, float],
    per_class: dict[str, dict[str, float]],
    matrix: np.ndarray,
    class_names: list[str],
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    report_path = output_dir / "per-class-metrics.csv"
    with report_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["class", "precision", "recall", "f1-score", "support"]
        )
        writer.writeheader()
        for name in class_names:
            writer.writerow({"class": name, **per_class[name]})

    matrix_path = output_dir / "confusion-matrix.png"
    figure_size = max(8, len(class_names) * 0.55)
    plt.figure(figsize=(figure_size, figure_size))
    sns.heatmap(matrix, cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicción")
    plt.ylabel("Clase real")
    plt.tight_layout()
    plt.savefig(matrix_path, dpi=180)
    plt.close()
    return [metrics_path, report_path, matrix_path]
