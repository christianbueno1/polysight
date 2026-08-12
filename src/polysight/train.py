"""Entrenamiento en dos etapas de EfficientNet-B0 con MLflow."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import torch
from torch import nn

from .config import ExperimentConfig, load_config
from .data.dataset import HyperKvasirDataset, build_dataloaders
from .data.prepare import sha256_file
from .evaluate import collect_predictions, load_classes
from .metrics import calculate_metrics, save_evaluation_artifacts
from .model import build_model, freeze_backbone
from .tracking import configure_tracking, flatten, reproducibility_tags


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True


def class_weights(dataset: HyperKvasirDataset, num_classes: int) -> torch.Tensor:
    counts = Counter(int(row["class_index"]) for row in dataset.rows)
    if len(counts) != num_classes or min(counts.values()) < 1:
        raise ValueError("Training no contiene todas las clases")
    inverse = torch.tensor([1.0 / counts[index] for index in range(num_classes)])
    return inverse / inverse.mean()


def build_loss(
    name: str, train_dataset: HyperKvasirDataset, num_classes: int, device: torch.device
) -> nn.Module:
    if name == "weighted_cross_entropy":
        return nn.CrossEntropyLoss(weight=class_weights(train_dataset, num_classes).to(device))
    return nn.CrossEntropyLoss()


def configure_stage(
    model: nn.Module, config: ExperimentConfig, stage: str
) -> tuple[torch.optim.Optimizer, torch.optim.lr_scheduler.CosineAnnealingLR]:
    if stage == "head":
        freeze_backbone(model, frozen=True)
        optimizer = torch.optim.AdamW(
            model.classifier.parameters(),
            lr=config.training.head_learning_rate,
            weight_decay=config.training.weight_decay,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=max(1, config.training.head_epochs)
        )
        return optimizer, scheduler

    freeze_backbone(model, frozen=False)
    optimizer = torch.optim.AdamW(
        [
            {
                "params": model.features.parameters(),
                "lr": config.training.backbone_learning_rate,
            },
            {
                "params": model.classifier.parameters(),
                "lr": config.training.head_learning_rate,
            },
        ],
        weight_decay=config.training.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max(1, config.training.finetune_epochs)
    )
    return optimizer, scheduler


def train_epoch(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: Any,
    device: torch.device,
    use_amp: bool,
) -> float:
    model.train()
    total_loss = 0.0
    total_examples = 0
    optimizer.zero_grad(set_to_none=True)
    for images, labels, _ in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        with torch.autocast(device_type=device.type, enabled=use_amp):
            logits = model(images)
            loss = criterion(logits, labels)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        optimizer.zero_grad(set_to_none=True)
        total_loss += loss.item() * labels.size(0)
        total_examples += labels.size(0)
    return total_loss / total_examples


def validation_metrics(
    model: nn.Module,
    loader: torch.utils.data.DataLoader,
    device: torch.device,
    classes: list[str],
) -> dict[str, float]:
    targets, probabilities = collect_predictions(model, loader, device)
    summary, _, _ = calculate_metrics(targets, probabilities, classes)
    return summary


def save_checkpoint(
    path: Path,
    *,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.CosineAnnealingLR,
    scaler: Any,
    epoch: int,
    stage: str,
    best_macro_f1: float,
    patience_counter: int,
    config: ExperimentConfig,
    classes: list[str],
    mlflow_run_id: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "scaler_state": scaler.state_dict(),
            "epoch": epoch,
            "stage": stage,
            "best_macro_f1": best_macro_f1,
            "patience_counter": patience_counter,
            "config": config.to_dict(),
            "classes": classes,
            "mlflow_run_id": mlflow_run_id,
        },
        path,
    )


def build_grad_scaler(use_amp: bool) -> Any:
    if hasattr(torch, "amp") and hasattr(torch.amp, "GradScaler"):
        return torch.amp.GradScaler("cuda", enabled=use_amp)
    return torch.cuda.amp.GradScaler(enabled=use_amp)


def run_training(config_path: Path, resume: Path | None = None, seed: int | None = None) -> Path:
    config = load_config(config_path)
    if seed is not None:
        config.training.seed = seed
    seed_everything(config.training.seed)
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
    if device.type != "cuda":
        raise RuntimeError("El entrenamiento requiere un nodo de cómputo con CUDA")
    model = build_model(
        len(classes),
        pretrained=config.model.pretrained,
        weights_path=Path(config.model.weights_path) if config.model.weights_path else None,
        dropout=config.model.dropout,
    ).to(device)
    criterion = build_loss(
        config.training.loss, loaders["train"].dataset, len(classes), device
    )
    use_amp = config.training.amp and device.type == "cuda"
    scaler = build_grad_scaler(use_amp)
    checkpoint_data = (
        torch.load(resume, map_location=device, weights_only=False) if resume else None
    )
    start_epoch = int(checkpoint_data["epoch"] + 1) if checkpoint_data else 0
    total_epochs = config.training.head_epochs + config.training.finetune_epochs
    stage = "head" if start_epoch < config.training.head_epochs else "finetune"
    optimizer, scheduler = configure_stage(model, config, stage)
    best_macro_f1 = -1.0
    patience_counter = 0
    if checkpoint_data:
        model.load_state_dict(checkpoint_data["model_state"])
        if checkpoint_data["stage"] == stage:
            optimizer.load_state_dict(checkpoint_data["optimizer_state"])
            scheduler.load_state_dict(checkpoint_data["scheduler_state"])
            scaler.load_state_dict(checkpoint_data["scaler_state"])
        best_macro_f1 = float(checkpoint_data["best_macro_f1"])
        patience_counter = (
            int(checkpoint_data["patience_counter"])
            if checkpoint_data["stage"] == stage
            else 0
        )

    configure_tracking(config.tracking.tracking_uri, config.tracking.experiment_name)
    run_id = checkpoint_data.get("mlflow_run_id") if checkpoint_data else None
    with mlflow.start_run(run_id=run_id, run_name=config.name) as active_run:
        run_id = active_run.info.run_id
        output_dir = Path(config.tracking.output_dir) / config.name / run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        mlflow.log_params(flatten("", config.to_dict()))
        mlflow.set_tags(reproducibility_tags(sha256_file(manifest)))
        mlflow.set_tag("device", torch.cuda.get_device_name(0))
        mlflow.log_artifact(str(config_path), artifact_path="configuration")

        for epoch in range(start_epoch, total_epochs):
            next_stage = "head" if epoch < config.training.head_epochs else "finetune"
            if next_stage != stage:
                stage = next_stage
                optimizer, scheduler = configure_stage(model, config, stage)
                patience_counter = 0
            loss = train_epoch(
                model,
                loaders["train"],
                criterion,
                optimizer,
                scaler,
                device,
                use_amp,
            )
            validation = validation_metrics(model, loaders["validation"], device, classes)
            metrics = {"train_loss": loss, **{f"val_{k}": v for k, v in validation.items()}}
            metrics["learning_rate"] = optimizer.param_groups[0]["lr"]
            mlflow.log_metrics(metrics, step=epoch)
            scheduler.step()
            improved = validation["macro_f1"] > best_macro_f1
            if improved:
                best_macro_f1 = validation["macro_f1"]
                patience_counter = 0
            else:
                patience_counter += 1
            save_checkpoint(
                output_dir / "last.pt",
                model=model,
                optimizer=optimizer,
                scheduler=scheduler,
                scaler=scaler,
                epoch=epoch,
                stage=stage,
                best_macro_f1=best_macro_f1,
                patience_counter=patience_counter,
                config=config,
                classes=classes,
                mlflow_run_id=run_id,
            )
            if improved:
                save_checkpoint(
                    output_dir / "best.pt",
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    scaler=scaler,
                    epoch=epoch,
                    stage=stage,
                    best_macro_f1=best_macro_f1,
                    patience_counter=patience_counter,
                    config=config,
                    classes=classes,
                    mlflow_run_id=run_id,
                )
            if stage == "finetune" and patience_counter >= config.training.patience:
                break

        best_path = output_dir / "best.pt"
        best = torch.load(best_path, map_location=device, weights_only=False)
        model.load_state_dict(best["model_state"])
        targets, probabilities = collect_predictions(model, loaders["validation"], device)
        summary, per_class, matrix = calculate_metrics(targets, probabilities, classes)
        artifact_dir = output_dir / "validation"
        save_evaluation_artifacts(artifact_dir, summary, per_class, matrix, classes)
        mlflow.log_artifacts(str(artifact_dir), artifact_path="validation")
        mlflow.log_artifact(str(best_path), artifact_path="checkpoints")
        return best_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--seed", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    best_path = run_training(args.config, args.resume, args.seed)
    print(json.dumps({"best_checkpoint": str(best_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
