#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${SLURM_JOB_ID:-}" ]]; then
  echo "ERROR: este script solo puede ejecutarse dentro de un job Slurm." >&2
  exit 2
fi

case "$(hostname)" in
  login*)
    echo "ERROR: se rechazó la ejecución en el nodo de login." >&2
    exit 2
    ;;
esac

module purge
module load pytorch/2.2
module load cuda/12.4

POLYSIGHT_CLUSTER_ROOT="${POLYSIGHT_CLUSTER_ROOT:-${SLURM_SUBMIT_DIR}}"
POLYSIGHT_STORAGE_ROOT="${POLYSIGHT_STORAGE_ROOT:-/home/christian.bueno__espol.edu.ec/polysight-storage}"
POLYSIGHT_DATA_ARCHIVE="${POLYSIGHT_DATA_ARCHIVE:-/home/christian.bueno__espol.edu.ec/datasets/hyper-kvasir-labeled-images.zip}"
POLYSIGHT_DATA_DIR="${POLYSIGHT_DATA_DIR:-${POLYSIGHT_STORAGE_ROOT}/datasets/hyper-kvasir/labeled-images}"
POLYSIGHT_MANIFEST_DIR="${POLYSIGHT_MANIFEST_DIR:-${POLYSIGHT_STORAGE_ROOT}/manifests}"
POLYSIGHT_MLFLOW_DIR="${POLYSIGHT_MLFLOW_DIR:-${POLYSIGHT_STORAGE_ROOT}/mlruns}"
POLYSIGHT_RUNS_DIR="${POLYSIGHT_RUNS_DIR:-${POLYSIGHT_STORAGE_ROOT}/runs}"
POLYSIGHT_WEIGHTS_PATH="${POLYSIGHT_WEIGHTS_PATH:-}"

export POLYSIGHT_CLUSTER_ROOT POLYSIGHT_STORAGE_ROOT POLYSIGHT_DATA_ARCHIVE
export POLYSIGHT_DATA_DIR POLYSIGHT_MANIFEST_DIR POLYSIGHT_MLFLOW_DIR
export POLYSIGHT_RUNS_DIR POLYSIGHT_WEIGHTS_PATH

cd "${POLYSIGHT_CLUSTER_ROOT}"
if [[ -f .venv-cluster/bin/activate ]]; then
  source .venv-cluster/bin/activate
fi

python --version
echo "Commit: $(git rev-parse HEAD)"
echo "Módulos: ${LOADEDMODULES:-unknown}"
