#!/usr/bin/env python3
"""Consolida accounting de Slurm y métricas de un run en archivos versionables."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

SACCT_FIELDS = (
    "JobID,JobName,Partition,NodeList,AllocCPUS,ReqMem,AllocTRES,Elapsed,"
    "TotalCPU,AveRSS,MaxRSS,State,ExitCode"
)
SUMMARY_FIELDS = (
    "slurm_job_id",
    "mlflow_run_id",
    "name",
    "profile",
    "strategy",
    "seed",
    "git_commit",
    "state",
    "exit_code",
    "elapsed_seconds",
    "average_cpu_cores",
    "max_rss_mib",
    "gpu_model",
    "gpu_memory_sample_mib",
    "accuracy",
    "balanced_accuracy",
    "macro_f1",
    "top_3_accuracy",
    "weighted_f1",
)


def parse_duration(value: str) -> int:
    """Convierte [[DD-]HH:]MM:SS a segundos."""
    days = 0
    if "-" in value:
        day_text, value = value.split("-", 1)
        days = int(day_text)
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours, (minutes, seconds) = 0, parts
    else:
        raise ValueError(f"Duración Slurm inválida: {value}")
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def parse_memory_mib(value: str) -> float | None:
    if not value:
        return None
    match = re.fullmatch(r"([0-9.]+)([KMGTP]?)", value)
    if not match:
        raise ValueError(f"Memoria Slurm inválida: {value}")
    amount = float(match.group(1))
    factor = {"": 1 / 1024**2, "K": 1 / 1024, "M": 1, "G": 1024, "T": 1024**2}
    return amount * factor[match.group(2)]


def parse_sacct(output: str, job_id: str) -> dict[str, dict[str, str]]:
    rows = list(csv.DictReader(output.splitlines(), delimiter="|"))
    indexed = {row["JobID"]: row for row in rows}
    required = (job_id, f"{job_id}.batch", f"{job_id}.0")
    missing = [key for key in required if key not in indexed]
    if missing:
        raise ValueError(f"sacct no devolvió los steps requeridos: {', '.join(missing)}")
    return indexed


def run_ssh(host: str, remote_command: str, ssh_config: Path | None) -> str:
    command = ["ssh"]
    if ssh_config:
        command.extend(("-F", str(ssh_config)))
    command.extend((host, remote_command))
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


def strategy_from_name(name: str) -> str:
    for strategy in ("baseline", "weighted"):
        if name.endswith(f"-{strategy}"):
            return strategy
    return "unknown"


def summary_row(record: dict[str, Any]) -> dict[str, Any]:
    identity = record["identity"]
    provenance = record["provenance"]
    accounting = record["slurm"]["observed_consumption"]
    metrics = record["validation_metrics"]
    sample = record.get("point_samples", {}).get("gpu_memory", {})
    return {
        "slurm_job_id": identity["slurm_job_id"],
        "mlflow_run_id": identity["mlflow_run_id"],
        "name": identity["name"],
        "profile": identity["profile"],
        "strategy": identity["strategy"],
        "seed": identity["seed"],
        "git_commit": provenance["git_commit"],
        "state": accounting["state"],
        "exit_code": accounting["exit_code"],
        "elapsed_seconds": accounting["elapsed_seconds"],
        "average_cpu_cores": accounting["average_cpu_cores"],
        "max_rss_mib": accounting["training_step_max_rss_mib"],
        "gpu_model": record["slurm"]["requested_resources"]["gpu_model"],
        "gpu_memory_sample_mib": sample.get("used_memory_mib", ""),
        **metrics,
    }


def regenerate_summary(runs_dir: Path, summary_path: Path) -> None:
    rows = []
    for path in sorted(runs_dir.glob("*.yaml"), key=lambda item: int(item.stem)):
        rows.append(summary_row(yaml.safe_load(path.read_text(encoding="utf-8"))))
    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True, type=str)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--host", default="cedia")
    parser.add_argument("--ssh-config", type=Path)
    parser.add_argument(
        "--remote-storage",
        default="/home/christian.bueno__espol.edu.ec/projects/polysight-storage",
    )
    parser.add_argument("--gpu-memory-sample-mib", type=int)
    parser.add_argument("--gpu-sample-note")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9]+", args.job_id):
        parser.error("--job-id debe ser numérico")
    if not re.fullmatch(r"[0-9a-f]{32}", args.run_id):
        parser.error("--run-id debe ser un ID hexadecimal de MLflow")
    if not args.config.is_file():
        parser.error(f"No existe la configuración: {args.config}")

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    name = str(config["name"])
    run_dir = f"{args.remote_storage}/runs/{name}/{args.run_id}"
    metrics_path = f"{run_dir}/validation/metrics.json"
    sacct_command = f"sacct -j {args.job_id} --format={SACCT_FIELDS} -P"
    log_path = f"slurm-polysight-train-{args.job_id}.out"
    commit_command = (
        f"cd ~/projects/polysight && sed -n 's/^Commit: //p' {shlex.quote(log_path)} | head -n 1"
    )

    sacct_output = run_ssh(args.host, sacct_command, args.ssh_config)
    metrics_output = run_ssh(args.host, f"cat {shlex.quote(metrics_path)}", args.ssh_config)
    git_commit = run_ssh(args.host, commit_command, args.ssh_config).strip()
    steps = parse_sacct(sacct_output, args.job_id)
    job = steps[args.job_id]
    batch = steps[f"{args.job_id}.batch"]
    training = steps[f"{args.job_id}.0"]
    elapsed_seconds = parse_duration(job["Elapsed"])
    total_cpu_seconds = parse_duration(job["TotalCPU"])

    alloc_tres = job["AllocTRES"]
    gpu_match = re.search(r"gres/gpu:([^=,]+)=([0-9]+)", alloc_tres)
    memory_match = re.search(r"mem=([0-9.]+[KMGTP]?)", alloc_tres)
    if not gpu_match or not memory_match:
        raise ValueError(f"AllocTRES no contiene GPU o memoria esperada: {alloc_tres}")

    record: dict[str, Any] = {
        "schema_version": 1,
        "collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "identity": {
            "slurm_job_id": int(args.job_id),
            "mlflow_run_id": args.run_id,
            "name": name,
            "profile": config["profile"],
            "strategy": strategy_from_name(name),
            "seed": args.seed,
        },
        "provenance": {
            "git_commit": git_commit,
            "config_path": str(args.config),
            "remote_run_dir": run_dir,
            "metrics_path": metrics_path,
        },
        "slurm": {
            "requested_resources": {
                "partition": job["Partition"],
                "node": job["NodeList"],
                "nodes": 1,
                "cpus": int(job["AllocCPUS"]),
                "memory_mib": round(parse_memory_mib(memory_match.group(1)) or 0, 3),
                "gpus": int(gpu_match.group(2)),
                "gpu_model": gpu_match.group(1),
                "alloc_tres_raw": alloc_tres,
            },
            "observed_consumption": {
                "state": job["State"],
                "exit_code": job["ExitCode"],
                "elapsed": job["Elapsed"],
                "elapsed_seconds": elapsed_seconds,
                "total_cpu": job["TotalCPU"],
                "total_cpu_seconds": total_cpu_seconds,
                "average_cpu_cores": round(total_cpu_seconds / elapsed_seconds, 3),
                "training_step_max_rss_mib": round(parse_memory_mib(training["MaxRSS"]) or 0, 3),
                "batch_step_max_rss_mib": round(parse_memory_mib(batch["MaxRSS"]) or 0, 3),
            },
        },
        "validation_metrics": json.loads(metrics_output),
        "sources": {
            "slurm_accounting": {"command": sacct_command, "captured_output": sacct_output},
            "validation_metrics": {"remote_file": metrics_path},
            "git_commit": {"remote_log": f"~/projects/polysight/{log_path}"},
        },
        "limitations": [
            "Slurm no reportó un máximo de memoria GPU para este job.",
            "MaxRSS se registra por step y no representa la suma simultánea de procesos.",
        ],
    }
    if args.gpu_memory_sample_mib is not None:
        record["point_samples"] = {
            "gpu_memory": {
                "used_memory_mib": args.gpu_memory_sample_mib,
                "method": "nvidia-smi --query-compute-apps=pid,used_memory --format=csv",
                "note": args.gpu_sample_note or "Muestra puntual tomada durante el job.",
                "is_maximum": False,
            }
        }

    runs_dir = Path("experiments/runs")
    runs_dir.mkdir(parents=True, exist_ok=True)
    output_path = runs_dir / f"{args.job_id}.yaml"
    if output_path.exists() and not args.force:
        raise FileExistsError(f"Ya existe {output_path}; use --force para reemplazarlo")
    output_path.write_text(
        yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    regenerate_summary(runs_dir, Path("experiments/summary.csv"))
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
