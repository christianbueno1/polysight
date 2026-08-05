"""Generación de manifests deterministas para HyperKvasir."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .constants import DEFAULT_SEED, IMAGE_SUFFIXES, MAIN_CLASS_MIN_IMAGES, SPLIT_RATIOS
from .prepare import sha256_file


@dataclass(frozen=True)
class ImageRecord:
    path: Path
    relative_path: str
    label: str
    sha256: str
    perceptual_hash: int


def resolve_dataset_root(data_dir: Path) -> Path:
    candidate = data_dir.resolve()
    nested = candidate / "labeled-images"
    if nested.is_dir():
        candidate = nested
    if not candidate.is_dir():
        raise FileNotFoundError(f"No existe el directorio de datos: {candidate}")
    return candidate


def difference_hash(path: Path, hash_size: int = 8) -> int:
    with Image.open(path) as image:
        pixels = list(image.convert("L").resize((hash_size + 1, hash_size)).getdata())
    value = 0
    width = hash_size + 1
    for row in range(hash_size):
        for column in range(hash_size):
            value = (value << 1) | int(
                pixels[row * width + column] > pixels[row * width + column + 1]
            )
    return value


def scan_images(dataset_root: Path) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for path in sorted(dataset_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        records.append(
            ImageRecord(
                path=path,
                relative_path=path.relative_to(dataset_root).as_posix(),
                label=path.parent.name,
                sha256=sha256_file(path),
                perceptual_hash=difference_hash(path),
            )
        )
    if not records:
        raise ValueError(f"No se encontraron imágenes en {dataset_root}")
    return records


def select_labels(records: list[ImageRecord], profile: str) -> list[str]:
    counts = Counter(record.label for record in records)
    if profile == "full23":
        return sorted(counts)
    if profile == "main16":
        return sorted(label for label, count in counts.items() if count >= MAIN_CLASS_MIN_IMAGES)
    raise ValueError(f"Perfil desconocido: {profile}")


def _targets(total: int) -> dict[str, int]:
    test = max(1, round(total * SPLIT_RATIOS["test"]))
    validation = max(1, round(total * SPLIT_RATIOS["validation"]))
    if total - test - validation < 1:
        raise ValueError(f"La clase necesita al menos 3 imágenes; recibió {total}")
    return {"test": test, "validation": validation, "train": total - test - validation}


def assign_splits(records: list[ImageRecord], labels: list[str], seed: int) -> dict[str, str]:
    selected = [record for record in records if record.label in labels]
    labels_by_hash: dict[str, set[str]] = defaultdict(set)
    for record in selected:
        labels_by_hash[record.sha256].add(record.label)
    conflicts = {digest: value for digest, value in labels_by_hash.items() if len(value) > 1}
    if conflicts:
        raise ValueError(f"Duplicados exactos con etiquetas distintas: {len(conflicts)}")

    assignments: dict[str, str] = {}
    by_label: dict[str, list[ImageRecord]] = defaultdict(list)
    for record in selected:
        by_label[record.label].append(record)

    for label in labels:
        groups: dict[str, list[ImageRecord]] = defaultdict(list)
        for record in by_label[label]:
            groups[record.sha256].append(record)
        shuffled = sorted(groups.values(), key=lambda group: group[0].relative_path)
        random.Random(f"{seed}:{label}").shuffle(shuffled)
        targets = _targets(len(by_label[label]))
        counts = Counter()
        for group in shuffled:
            if counts["test"] < targets["test"]:
                split = "test"
            elif counts["validation"] < targets["validation"]:
                split = "validation"
            else:
                split = "train"
            for record in group:
                assignments[record.relative_path] = split
            counts[split] += len(group)
    return assignments


class BKTree:
    """BK-tree mínimo para buscar hashes perceptuales por distancia de Hamming."""

    def __init__(self) -> None:
        self.root: tuple[int, str, dict[int, object]] | None = None

    @staticmethod
    def distance(left: int, right: int) -> int:
        return (left ^ right).bit_count()

    def add(self, value: int, name: str) -> None:
        node = (value, name, {})
        if self.root is None:
            self.root = node
            return
        current = self.root
        while True:
            distance = self.distance(value, current[0])
            children = current[2]
            if distance not in children:
                children[distance] = node
                return
            current = children[distance]  # type: ignore[assignment]

    def search(self, value: int, threshold: int) -> list[tuple[int, str]]:
        if self.root is None:
            return []
        matches: list[tuple[int, str]] = []
        stack = [self.root]
        while stack:
            current = stack.pop()
            distance = self.distance(value, current[0])
            if distance <= threshold:
                matches.append((distance, current[1]))
            lower, upper = distance - threshold, distance + threshold
            stack.extend(
                child for edge, child in current[2].items() if lower <= edge <= upper
            )
        return matches


def write_perceptual_report(
    records: list[ImageRecord], output_path: Path, threshold: int = 5
) -> int:
    tree = BKTree()
    pairs: list[dict[str, object]] = []
    for record in sorted(records, key=lambda item: item.relative_path):
        for distance, other in tree.search(record.perceptual_hash, threshold):
            pairs.append(
                {"image_a": other, "image_b": record.relative_path, "hamming_distance": distance}
            )
        tree.add(record.perceptual_hash, record.relative_path)
    output_path.write_text(json.dumps(pairs, indent=2) + "\n", encoding="utf-8")
    return len(pairs)


def generate_manifests(
    data_dir: Path, output_dir: Path, profile: str, seed: int = DEFAULT_SEED
) -> dict[str, object]:
    dataset_root = resolve_dataset_root(data_dir)
    records = scan_images(dataset_root)
    labels = select_labels(records, profile)
    assignments = assign_splits(records, labels, seed)
    selected = [record for record in records if record.label in labels]
    class_to_index = {label: index for index, label in enumerate(labels)}

    profile_dir = output_dir.resolve() / profile
    profile_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = profile_dir / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["relative_path", "label", "class_index", "split", "sha256"],
        )
        writer.writeheader()
        for record in sorted(selected, key=lambda item: item.relative_path):
            writer.writerow(
                {
                    "relative_path": record.relative_path,
                    "label": record.label,
                    "class_index": class_to_index[record.label],
                    "split": assignments[record.relative_path],
                    "sha256": record.sha256,
                }
            )

    (profile_dir / "classes.json").write_text(
        json.dumps(class_to_index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    near_duplicate_count = write_perceptual_report(
        selected, profile_dir / "perceptual-duplicates.json"
    )
    split_counts = Counter(assignments.values())
    class_counts = Counter(record.label for record in selected)
    summary: dict[str, object] = {
        "profile": profile,
        "seed": seed,
        "dataset_root": str(dataset_root),
        "image_count": len(selected),
        "class_count": len(labels),
        "class_counts": dict(sorted(class_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "split_ratios": SPLIT_RATIOS,
        "manifest_sha256": sha256_file(manifest_path),
        "perceptual_hash": "dHash-64",
        "perceptual_hamming_threshold": 5,
        "potential_duplicate_pairs": near_duplicate_count,
    }
    (profile_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("manifests"))
    parser.add_argument("--profile", choices=("main16", "full23"), required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = generate_manifests(args.data_dir, args.output_dir, args.profile, args.seed)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
