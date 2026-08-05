"""Configuración tipada de experimentos PolySight."""

from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DataConfig:
    data_dir: str
    manifest: str
    image_size: int = 224
    batch_size: int = 128
    num_workers: int = 8


@dataclass
class ModelConfig:
    architecture: str = "efficientnet_b0"
    pretrained: bool = True
    weights_path: str | None = None
    dropout: float = 0.2


@dataclass
class TrainingConfig:
    seed: int = 42
    head_epochs: int = 3
    finetune_epochs: int = 30
    head_learning_rate: float = 1e-3
    backbone_learning_rate: float = 1e-4
    weight_decay: float = 1e-4
    patience: int = 7
    loss: str = "cross_entropy"
    amp: bool = True


@dataclass
class TrackingConfig:
    experiment_name: str = "polysight"
    tracking_uri: str = "file:./artifacts/mlruns"
    output_dir: str = "artifacts/runs"


@dataclass
class ExperimentConfig:
    name: str
    profile: str
    data: DataConfig
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def _expand(value: str | None) -> str | None:
    if value is None:
        return None
    return os.path.expanduser(os.path.expandvars(value))


def load_config(path: Path) -> ExperimentConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Configuración YAML inválida: {path}")
    data = DataConfig(**raw.pop("data"))
    model = ModelConfig(**raw.pop("model", {}))
    training = TrainingConfig(**raw.pop("training", {}))
    tracking = TrackingConfig(**raw.pop("tracking", {}))
    config = ExperimentConfig(
        data=data, model=model, training=training, tracking=tracking, **raw
    )
    config.data.data_dir = _expand(config.data.data_dir) or ""
    config.data.manifest = _expand(config.data.manifest) or ""
    config.model.weights_path = _expand(config.model.weights_path)
    if config.model.weights_path and "${" in config.model.weights_path:
        config.model.weights_path = None
    config.tracking.tracking_uri = _expand(config.tracking.tracking_uri) or ""
    config.tracking.output_dir = _expand(config.tracking.output_dir) or ""
    if config.profile not in {"main16", "full23"}:
        raise ValueError(f"Perfil inválido: {config.profile}")
    if config.training.loss not in {"cross_entropy", "weighted_cross_entropy"}:
        raise ValueError(f"Pérdida inválida: {config.training.loss}")
    return config
