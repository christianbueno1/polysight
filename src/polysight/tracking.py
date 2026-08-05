"""Utilidades reproducibles de MLflow."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import mlflow


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def configure_tracking(uri: str, experiment_name: str) -> None:
    if uri.startswith("file:"):
        Path(uri.removeprefix("file:")).expanduser().resolve().mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment_name)


def reproducibility_tags(manifest_sha256: str) -> dict[str, str]:
    return {
        "git_commit": git_commit(),
        "manifest_sha256": manifest_sha256,
        "loaded_modules": os.environ.get("LOADEDMODULES", "local"),
    }


def flatten(prefix: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    flattened: dict[str, Any] = {}
    for key, nested in value.items():
        nested_prefix = f"{prefix}.{key}" if prefix else key
        flattened.update(flatten(nested_prefix, nested))
    return flattened
