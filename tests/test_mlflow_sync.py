from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


def load_rebase_module(project_root: Path):
    script = project_root / "scripts" / "rebase-mlflow.py"
    specification = importlib.util.spec_from_file_location("rebase_mlflow", script)
    assert specification and specification.loader
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_rebase_mlflow_file_uri(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    module = load_rebase_module(project_root)
    mlruns = tmp_path / "local" / "mlruns"
    metadata_path = mlruns / "1" / "run" / "meta.yaml"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(
        yaml.safe_dump(
            {"artifact_uri": "file:///remote/storage/runs/experiment/artifacts"}
        ),
        encoding="utf-8",
    )
    assert module.rebase(mlruns, "/remote/storage") == 1
    updated = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    assert updated["artifact_uri"] == (tmp_path / "local" / "runs/experiment/artifacts").as_uri()
