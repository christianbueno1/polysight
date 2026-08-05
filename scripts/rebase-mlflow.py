"""Reescribe URI file:// remotos después de sincronizar un FileStore MLflow."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def replace_uri(value: Any, remote_root: str, local_root: str) -> Any:
    if isinstance(value, dict):
        return {key: replace_uri(nested, remote_root, local_root) for key, nested in value.items()}
    if isinstance(value, list):
        return [replace_uri(item, remote_root, local_root) for item in value]
    if isinstance(value, str):
        remote_uri = Path(remote_root).resolve().as_uri()
        if value.startswith(remote_uri):
            return local_root + value.removeprefix(remote_uri)
    return value


def rebase(mlruns_dir: Path, remote_root: str) -> int:
    local_uri = mlruns_dir.parent.resolve().as_uri()
    changed = 0
    for metadata_path in mlruns_dir.rglob("meta.yaml"):
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        updated = replace_uri(metadata, remote_root, local_uri)
        if updated != metadata:
            metadata_path.write_text(
                yaml.safe_dump(updated, sort_keys=False, allow_unicode=True), encoding="utf-8"
            )
            changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mlruns-dir", type=Path, required=True)
    parser.add_argument("--remote-root", required=True)
    args = parser.parse_args()
    print(f"Archivos meta.yaml actualizados: {rebase(args.mlruns_dir, args.remote_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
