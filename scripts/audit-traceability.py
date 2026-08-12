#!/usr/bin/env python3
"""Audita la trazabilidad local de runs, MLflow y evaluaciones finales."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import yaml

METRICS = ("accuracy", "balanced_accuracy", "macro_f1", "top_3_accuracy", "weighted_f1")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"YAML inválido: {path}")
    return value


def assert_equal(actual: Any, expected: Any, context: str) -> None:
    if actual != expected:
        raise AssertionError(f"{context}: esperado {expected!r}, obtenido {actual!r}")


def assert_commit_exists(repo: Path, commit: str) -> None:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"Commit no disponible localmente: {commit}")


def artifact_dir(mlflow_root: Path, artifact_uri: str) -> Path:
    prefix = "mlflow-artifacts:/"
    if not artifact_uri.startswith(prefix):
        raise AssertionError(f"URI de artefacto no portable: {artifact_uri}")
    return mlflow_root / "artifacts" / artifact_uri.removeprefix(prefix)


def audit_training_runs(
    repo: Path, mlflow_root: Path, connection: sqlite3.Connection
) -> dict[str, Any]:
    summary_path = repo / "experiments/summary.csv"
    with summary_path.open(newline="", encoding="utf-8") as stream:
        summary = list(csv.DictReader(stream))
    assert_equal(len(summary), 9, "Cantidad de runs en summary.csv")

    portable_locations = [
        row[0]
        for query in (
            "SELECT artifact_location FROM experiments WHERE lifecycle_stage = 'active'",
            "SELECT artifact_uri FROM runs WHERE lifecycle_stage = 'active'",
        )
        for row in connection.execute(query)
    ]
    invalid_locations = [
        location for location in portable_locations if not location.startswith("mlflow-artifacts:/")
    ]
    assert_equal(invalid_locations, [], "URI no portables en MLflow")

    config_hashes: dict[str, str] = {}
    manifest_hashes: dict[str, set[str]] = {}
    seen_run_ids: set[str] = set()
    for row in summary:
        job_id = row["slurm_job_id"]
        run_id = row["mlflow_run_id"]
        record = load_yaml(repo / f"experiments/runs/{job_id}.yaml")
        identity = record["identity"]
        provenance = record["provenance"]
        slurm = record["slurm"]["observed_consumption"]

        for key in ("mlflow_run_id", "name", "profile", "strategy"):
            assert_equal(str(identity[key]), row[key], f"Job {job_id}: identity.{key}")
        assert_equal(str(identity["seed"]), row["seed"], f"Job {job_id}: seed")
        assert_equal(provenance["git_commit"], row["git_commit"], f"Job {job_id}: commit")
        assert_equal(slurm["state"], row["state"], f"Job {job_id}: estado")
        assert_equal(slurm["exit_code"], row["exit_code"], f"Job {job_id}: exit code")
        assert_commit_exists(repo, provenance["git_commit"])

        run = connection.execute(
            "SELECT status, artifact_uri FROM runs WHERE run_uuid = ?", (run_id,)
        ).fetchone()
        if run is None:
            raise AssertionError(f"Run ausente en MLflow: {run_id}")
        assert_equal(run[0], "FINISHED", f"Run {run_id}: estado MLflow")
        run_artifacts = artifact_dir(mlflow_root, run[1])

        tags = dict(
            connection.execute("SELECT key, value FROM tags WHERE run_uuid = ?", (run_id,))
        )
        params = dict(
            connection.execute("SELECT key, value FROM params WHERE run_uuid = ?", (run_id,))
        )
        assert_equal(tags.get("git_commit"), row["git_commit"], f"Run {run_id}: tag commit")
        manifest_hash = tags.get("manifest_sha256", "")
        if len(manifest_hash) != 64:
            raise AssertionError(f"Run {run_id}: manifest_sha256 ausente o inválido")
        manifest_hashes.setdefault(row["profile"], set()).add(manifest_hash)
        assert_equal(params.get("name"), row["name"], f"Run {run_id}: param name")
        assert_equal(params.get("profile"), row["profile"], f"Run {run_id}: param profile")
        assert_equal(params.get("training.seed"), row["seed"], f"Run {run_id}: param seed")

        config_path = repo / provenance["config_path"]
        archived_config = run_artifacts / "configuration" / config_path.name
        assert_equal(
            archived_config.read_bytes(),
            config_path.read_bytes(),
            f"Run {run_id}: configuración archivada",
        )
        config_hashes[str(config_path.relative_to(repo))] = sha256_file(config_path)

        validation_dir = run_artifacts / "validation"
        required = {"metrics.json", "per-class-metrics.csv", "confusion-matrix.png"}
        actual = {path.name for path in validation_dir.iterdir() if path.is_file()}
        if not required <= actual:
            missing = required - actual
            raise AssertionError(f"Run {run_id}: artefactos validation faltantes: {missing}")
        checkpoint = run_artifacts / "checkpoints/best.pt"
        if not checkpoint.is_file():
            raise AssertionError(f"Run {run_id}: checkpoint ausente")

        validation = json.loads((validation_dir / "metrics.json").read_text(encoding="utf-8"))
        for metric in METRICS:
            assert_equal(
                float(validation[metric]),
                float(row[metric]),
                f"Run {run_id}: métrica {metric}",
            )
        seen_run_ids.add(run_id)

    assert_equal(len(seen_run_ids), 9, "IDs únicos de entrenamiento")
    for profile, hashes in manifest_hashes.items():
        assert_equal(len(hashes), 1, f"Perfil {profile}: manifests distintos entre semillas")
    return {
        "training_runs": len(summary),
        "portable_mlflow_locations": len(portable_locations),
        "config_sha256": dict(sorted(config_hashes.items())),
        "manifest_sha256": {
            profile: next(iter(values)) for profile, values in manifest_hashes.items()
        },
    }


def audit_final_evaluation(
    repo: Path, mlflow_root: Path, connection: sqlite3.Connection
) -> dict[str, Any]:
    record = load_yaml(repo / "experiments/final-evaluation.yaml")
    regeneration = record["artifact_regeneration"]
    assert_commit_exists(repo, record["sources"]["code_commit"])
    assert_commit_exists(repo, regeneration["code_commit"])

    official_root = repo / "artifacts/cedia/final-evaluation"
    derived_root = repo / "artifacts/cedia/final-evaluation-derived"
    derived_by_profile = {item["profile"]: item for item in regeneration["models"]}
    verified_artifacts = 0
    for model in record["models"]:
        profile = model["profile"]
        directory_name = Path(model["output_dir"]).name
        official_dir = official_root / directory_name
        derived_dir = derived_root / directory_name
        for filename in model["artifacts"]:
            if not (official_dir / filename).is_file():
                raise AssertionError(f"{profile}: artefacto oficial ausente: {filename}")
        official_metrics = json.loads(
            (official_dir / "metrics.json").read_text(encoding="utf-8")
        )
        assert_equal(official_metrics, model["test_metrics"], f"{profile}: métricas test")

        derived = derived_by_profile[profile]
        assert_equal(
            (official_dir / "metrics.json").read_bytes(),
            (derived_dir / "metrics.json").read_bytes(),
            f"{profile}: metrics derivadas",
        )
        assert_equal(
            (official_dir / "per-class-metrics.csv").read_bytes(),
            (derived_dir / "per-class-metrics.csv").read_bytes(),
            f"{profile}: métricas por clase derivadas",
        )
        for filename, expected_hash in derived["artifacts"].items():
            assert_equal(
                sha256_file(derived_dir / filename),
                expected_hash,
                f"{profile}: hash de {filename}",
            )
            verified_artifacts += 1

        run_id = model["mlflow_run_id"]
        run = connection.execute(
            "SELECT artifact_uri FROM runs WHERE run_uuid = ?", (run_id,)
        ).fetchone()
        if run is None:
            raise AssertionError(f"{profile}: run final ausente en MLflow")
        selected_checkpoint = artifact_dir(mlflow_root, run[0]) / "checkpoints/best.pt"
        assert_equal(
            sha256_file(selected_checkpoint),
            derived["checkpoint_sha256"],
            f"{profile}: hash del checkpoint final",
        )
        manifest_tag = connection.execute(
            "SELECT value FROM tags WHERE run_uuid = ? AND key = 'manifest_sha256'", (run_id,)
        ).fetchone()
        assert_equal(
            manifest_tag[0] if manifest_tag else None,
            derived["manifest_sha256"],
            f"{profile}: hash del manifest final",
        )

    return {"official_models": len(record["models"]), "derived_artifacts": verified_artifacts}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mlflow-root", type=Path, default=Path("artifacts/cedia/mlflow")
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo = args.repo.resolve()
    mlflow_root = (repo / args.mlflow_root).resolve()
    database = mlflow_root / "mlflow.db"
    with sqlite3.connect(database) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        assert_equal(quick_check, "ok", "Integridad SQLite")
        training = audit_training_runs(repo, mlflow_root, connection)
        final = audit_final_evaluation(repo, mlflow_root, connection)
    result = {"status": "ok", "sqlite_quick_check": quick_check, **training, **final}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
