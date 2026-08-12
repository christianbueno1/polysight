"""Métricas y artefactos de evaluación multiclase."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import PercentFormatter
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


def normalize_confusion_matrix(matrix: np.ndarray) -> np.ndarray:
    """Normaliza cada fila por su soporte y conserva en cero las filas vacías."""
    row_totals = matrix.sum(axis=1, keepdims=True)
    return np.divide(
        matrix,
        row_totals,
        out=np.zeros_like(matrix, dtype=float),
        where=row_totals != 0,
    )


def save_evaluation_artifacts(
    output_dir: Path,
    summary: dict[str, float],
    per_class: dict[str, dict[str, float]],
    matrix: np.ndarray,
    class_names: list[str],
) -> list[Path]:
    if matrix.shape != (len(class_names), len(class_names)):
        raise ValueError("La matriz de confusión no coincide con el número de clases")

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

    matrix_csv_path = output_dir / "confusion-matrix.csv"
    with matrix_csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["actual\\predicted", *class_names])
        for name, row in zip(class_names, matrix, strict=True):
            writer.writerow([name, *(int(value) for value in row)])

    figure_size = max(8, len(class_names) * 0.55)
    matrix_path = output_dir / "confusion-matrix.png"
    plt.figure(figsize=(figure_size, figure_size))
    sns.heatmap(matrix, cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicción")
    plt.ylabel("Clase real")
    plt.tight_layout()
    plt.savefig(matrix_path, dpi=180)
    plt.close()

    normalized_matrix = normalize_confusion_matrix(matrix)
    formatted_percentages = np.vectorize("{:.1%}".format)(normalized_matrix)
    annotations = np.where(normalized_matrix > 0, formatted_percentages, "")
    normalized_path = output_dir / "confusion-matrix-normalized.png"
    plt.figure(figsize=(figure_size, figure_size))
    sns.heatmap(
        normalized_matrix,
        annot=annotations,
        fmt="",
        cmap="Blues",
        vmin=0,
        vmax=1,
        xticklabels=class_names,
        yticklabels=class_names,
        cbar_kws={"format": PercentFormatter(xmax=1)},
    )
    plt.xlabel("Predicción")
    plt.ylabel("Clase real")
    plt.tight_layout()
    plt.savefig(normalized_path, dpi=180)
    plt.close()
    return [metrics_path, report_path, matrix_csv_path, matrix_path, normalized_path]
