from __future__ import annotations

import csv
import json
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image

from polysight.data.prepare import extract_archive, inspect_archive
from polysight.data.split import assign_splits, generate_manifests, scan_images


def make_dataset(root: Path, class_sizes: dict[str, int]) -> Path:
    dataset = root / "labeled-images"
    rows = ["Video file,Organ,Finding,Classification\n"]
    for class_index, (label, size) in enumerate(class_sizes.items()):
        class_dir = dataset / "lower-gi-tract" / "category" / label
        class_dir.mkdir(parents=True)
        for image_index in range(size):
            name = f"{label}-{image_index}.jpg"
            color = ((class_index * 31) % 255, (image_index * 19) % 255, 100)
            Image.new("RGB", (16, 16), color=color).save(class_dir / name)
            rows.append(f"{label}-{image_index},Lower GI,{label},category\n")
    (dataset / "image-labels.csv").write_text("".join(rows), encoding="utf-8")
    return dataset


def test_archive_validation_and_idempotent_extraction(tmp_path: Path) -> None:
    source = tmp_path / "source"
    dataset = make_dataset(source, {"alpha": 3, "beta": 4})
    archive = tmp_path / "fixture.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for path in source.rglob("*"):
            if path.is_file():
                bundle.write(path, path.relative_to(source))

    metadata = inspect_archive(
        archive,
        expected_size=None,
        expected_sha256=None,
        expected_images=7,
        expected_classes=2,
    )
    assert metadata["image_count"] == 7
    first = extract_archive(archive, tmp_path / "output", metadata)
    second = extract_archive(archive, tmp_path / "output", metadata)
    assert first == second
    assert first.name == dataset.name


def test_split_is_reproducible_disjoint_and_preserves_duplicates(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path, {"alpha": 10, "beta": 10})
    duplicate = dataset / "lower-gi-tract" / "category" / "alpha" / "alpha-copy.jpg"
    original = dataset / "lower-gi-tract" / "category" / "alpha" / "alpha-0.jpg"
    duplicate.write_bytes(original.read_bytes())

    records = scan_images(dataset)
    assignments_a = assign_splits(records, ["alpha", "beta"], seed=42)
    assignments_b = assign_splits(records, ["alpha", "beta"], seed=42)
    assert assignments_a == assignments_b
    assert assignments_a[str(original.relative_to(dataset))] == assignments_a[
        str(duplicate.relative_to(dataset))
    ]
    assert set(assignments_a.values()) == {"train", "validation", "test"}


def test_profiles_and_manifest_metadata(tmp_path: Path) -> None:
    dataset = make_dataset(tmp_path / "data", {"large": 100, "rare": 6})
    main_summary = generate_manifests(dataset, tmp_path / "manifests", "main16")
    full_summary = generate_manifests(dataset, tmp_path / "manifests", "full23")

    assert main_summary["class_count"] == 1
    assert full_summary["class_count"] == 2
    assert full_summary["split_counts"] == {"test": 16, "train": 74, "validation": 16}

    manifest = tmp_path / "manifests" / "full23" / "manifest.csv"
    with manifest.open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 106
    assert Counter(row["split"] for row in rows) == full_summary["split_counts"]
    classes = json.loads(
        (tmp_path / "manifests" / "full23" / "classes.json").read_text(encoding="utf-8")
    )
    assert classes == {"large": 0, "rare": 1}
