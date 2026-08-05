"""Validación y extracción segura del ZIP etiquetado de HyperKvasir."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath

from .constants import (
    ARCHIVE_SHA256,
    ARCHIVE_SIZE_BYTES,
    EXPECTED_CLASS_COUNT,
    EXPECTED_IMAGE_COUNT,
    IMAGE_SUFFIXES,
)


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_archive(
    archive: Path,
    *,
    expected_size: int | None = ARCHIVE_SIZE_BYTES,
    expected_sha256: str | None = ARCHIVE_SHA256,
    expected_images: int | None = EXPECTED_IMAGE_COUNT,
    expected_classes: int | None = EXPECTED_CLASS_COUNT,
) -> dict[str, object]:
    archive = archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"No existe el archivo: {archive}")

    size = archive.stat().st_size
    if expected_size is not None and size != expected_size:
        raise ValueError(f"Tamaño inválido: {size}; esperado: {expected_size}")

    digest = sha256_file(archive)
    if expected_sha256 is not None and digest.lower() != expected_sha256.lower():
        raise ValueError(f"SHA-256 inválido: {digest}; esperado: {expected_sha256}")

    image_members: list[str] = []
    classes: set[str] = set()
    has_labels_csv = False
    with zipfile.ZipFile(archive) as bundle:
        bad_member = bundle.testzip()
        if bad_member:
            raise ValueError(f"Entrada ZIP corrupta: {bad_member}")
        for info in bundle.infolist():
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Ruta insegura dentro del ZIP: {info.filename}")
            if member.name == "image-labels.csv":
                has_labels_csv = True
            if member.suffix.lower() in IMAGE_SUFFIXES:
                image_members.append(info.filename)
                classes.add(member.parent.name)

    if not has_labels_csv:
        raise ValueError("El ZIP no contiene labeled-images/image-labels.csv")
    if expected_images is not None and len(image_members) != expected_images:
        raise ValueError(
            f"Cantidad de imágenes inválida: {len(image_members)}; esperada: {expected_images}"
        )
    if expected_classes is not None and len(classes) != expected_classes:
        raise ValueError(
            f"Cantidad de clases inválida: {len(classes)}; esperada: {expected_classes}"
        )

    return {
        "archive": str(archive),
        "size_bytes": size,
        "sha256": digest,
        "image_count": len(image_members),
        "class_count": len(classes),
        "classes": sorted(classes),
    }


def extract_archive(archive: Path, output_dir: Path, metadata: dict[str, object]) -> Path:
    output_dir = output_dir.resolve()
    marker = output_dir / ".polysight-prepared.json"
    dataset_root = output_dir / "labeled-images"
    if marker.is_file() and dataset_root.is_dir():
        previous = json.loads(marker.read_text(encoding="utf-8"))
        if previous.get("sha256") == metadata["sha256"]:
            return dataset_root
        raise ValueError(f"{output_dir} contiene una extracción de otro archivo")

    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            relative = PurePosixPath(info.filename)
            destination = output_dir.joinpath(*relative.parts)
            if info.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target, length=8 * 1024 * 1024)

    if not dataset_root.is_dir():
        raise ValueError("La extracción no produjo el directorio labeled-images")
    marker.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dataset_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--accept-noncanonical",
        action="store_true",
        help="Permite fixtures u otra versión sin validar tamaño, hash y conteos oficiales.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    overrides = {}
    if args.accept_noncanonical:
        overrides = {
            "expected_size": None,
            "expected_sha256": None,
            "expected_images": None,
            "expected_classes": None,
        }
    metadata = inspect_archive(args.archive, **overrides)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    if not args.validate_only:
        dataset_root = extract_archive(args.archive, args.output_dir, metadata)
        print(f"Dataset preparado en: {dataset_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
