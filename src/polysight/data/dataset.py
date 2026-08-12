"""Dataset y transformaciones para manifests de HyperKvasir."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms


class HyperKvasirDataset(Dataset[tuple[torch.Tensor, int, str]]):
    def __init__(self, data_dir: Path, manifest: Path, split: str, transform: Any) -> None:
        self.data_dir = data_dir
        self.transform = transform
        with manifest.open(encoding="utf-8") as stream:
            self.rows = [row for row in csv.DictReader(stream) if row["split"] == split]
        if not self.rows:
            raise ValueError(f"El manifest no contiene imágenes para el split {split}")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, int, str]:
        row = self.rows[index]
        path = self.data_dir / row["relative_path"]
        with Image.open(path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, int(row["class_index"]), row["relative_path"]


def build_transforms(image_size: int) -> dict[str, transforms.Compose]:
    normalization = transforms.Normalize(
        mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)
    )
    return {
        "train": transforms.Compose(
            [
                transforms.RandomResizedCrop(image_size, scale=(0.8, 1.0)),
                transforms.RandomHorizontalFlip(),
                transforms.RandomVerticalFlip(),
                transforms.RandomRotation(15),
                transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.02),
                transforms.ToTensor(),
                normalization,
            ]
        ),
        "validation": transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(image_size),
                transforms.ToTensor(),
                normalization,
            ]
        ),
        "test": transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(image_size),
                transforms.ToTensor(),
                normalization,
            ]
        ),
    }


def build_dataloaders(
    data_dir: Path,
    manifest: Path,
    image_size: int,
    batch_size: int,
    num_workers: int,
) -> dict[str, DataLoader]:
    transform_map = build_transforms(image_size)
    loaders: dict[str, DataLoader] = {}
    for split in ("train", "validation", "test"):
        dataset = HyperKvasirDataset(data_dir, manifest, split, transform_map[split])
        loaders[split] = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=split == "train",
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available(),
            persistent_workers=num_workers > 0,
        )
    return loaders
