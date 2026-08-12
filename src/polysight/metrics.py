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


def format_normalized_annotation(
    value: float, *, diagonal: bool, threshold: float = 0.02
) -> str:
    """Formatea porcentajes compactos y omite errores visualmente irrelevantes."""
    if not diagonal and value < threshold:
        return ""
    if diagonal or value >= 0.1:
        return f"{value:.0%}"
    return f"{value:.1%}"


def load_confusion_matrix_csv(path: Path) -> tuple[np.ndarray, list[str]]:
    """Carga una matriz etiquetada producida por ``save_evaluation_artifacts``."""
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.reader(stream))
    if not rows or not rows[0] or rows[0][0] != "actual\\predicted":
        raise ValueError("El CSV no contiene la cabecera actual\\predicted")

    class_names = rows[0][1:]
    if not class_names or len(set(class_names)) != len(class_names):
        raise ValueError("El CSV debe contener clases únicas")
    if len(rows) != len(class_names) + 1:
        raise ValueError("El CSV no contiene una fila por clase")

    values: list[list[int]] = []
    for expected_name, row in zip(class_names, rows[1:], strict=True):
        if len(row) != len(class_names) + 1 or row[0] != expected_name:
            raise ValueError("Las filas y columnas del CSV no coinciden")
        try:
            counts = [int(value) for value in row[1:]]
        except ValueError as exc:
            raise ValueError("La matriz debe contener conteos enteros") from exc
        if any(value < 0 for value in counts):
            raise ValueError("La matriz no admite conteos negativos")
        values.append(counts)
    return np.asarray(values, dtype=int), class_names


def save_normalized_confusion_matrix(
    path: Path,
    matrix: np.ndarray,
    class_names: list[str],
    *,
    annotation_threshold: float = 0.02,
) -> Path:
    """Guarda un heatmap normalizado legible y con contraste explícito."""
    if matrix.shape != (len(class_names), len(class_names)):
        raise ValueError("La matriz de confusión no coincide con el número de clases")
    if not 0 <= annotation_threshold <= 1:
        raise ValueError("El umbral de anotación debe estar entre 0 y 1")

    normalized_matrix = normalize_confusion_matrix(matrix)
    class_count = len(class_names)
    figure_size = max(10, class_count * 0.75)
    annotation_size = max(7, min(9, 160 / class_count))
    tick_size = max(7, min(10, 180 / class_count))

    figure, axis = plt.subplots(figsize=(figure_size, figure_size))
    sns.heatmap(
        normalized_matrix,
        annot=False,
        cmap="Blues",
        vmin=0,
        vmax=1,
        square=True,
        linewidths=0.4,
        linecolor="white",
        xticklabels=class_names,
        yticklabels=class_names,
        cbar_kws={"format": PercentFormatter(xmax=1)},
        ax=axis,
    )
    for row_index in range(class_count):
        for column_index in range(class_count):
            value = float(normalized_matrix[row_index, column_index])
            label = format_normalized_annotation(
                value,
                diagonal=row_index == column_index,
                threshold=annotation_threshold,
            )
            if not label:
                continue
            axis.text(
                column_index + 0.5,
                row_index + 0.5,
                label,
                horizontalalignment="center",
                verticalalignment="center",
                color="white" if value >= 0.5 else "#172033",
                fontsize=annotation_size,
                fontweight="bold" if row_index == column_index else "normal",
            )
    axis.set_xlabel("Predicción")
    axis.set_ylabel("Clase real")
    axis.tick_params(axis="x", labelrotation=90, labelsize=tick_size)
    axis.tick_params(axis="y", labelrotation=0, labelsize=tick_size)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=180)
    plt.close(figure)
    return path


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

    normalized_path = output_dir / "confusion-matrix-normalized.png"
    save_normalized_confusion_matrix(normalized_path, matrix, class_names)
    return [metrics_path, report_path, matrix_csv_path, matrix_path, normalized_path]
