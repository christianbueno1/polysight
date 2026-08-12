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
POLYSIGHT_STORAGE_ROOT="${POLYSIGHT_STORAGE_ROOT:-/home/christian.bueno__espol.edu.ec/projects/polysight-storage}"
POLYSIGHT_DATA_ARCHIVE="${POLYSIGHT_DATA_ARCHIVE:-/home/christian.bueno__espol.edu.ec/datasets/hyper-kvasir-labeled-images.zip}"
POLYSIGHT_DATA_DIR="${POLYSIGHT_DATA_DIR:-${POLYSIGHT_STORAGE_ROOT}/datasets/hyper-kvasir/labeled-images}"
POLYSIGHT_MANIFEST_DIR="${POLYSIGHT_MANIFEST_DIR:-${POLYSIGHT_STORAGE_ROOT}/manifests}"
POLYSIGHT_MLFLOW_ROOT="${POLYSIGHT_MLFLOW_ROOT:-${POLYSIGHT_STORAGE_ROOT}/mlflow}"
POLYSIGHT_RUNS_DIR="${POLYSIGHT_RUNS_DIR:-${POLYSIGHT_STORAGE_ROOT}/runs}"
POLYSIGHT_WEIGHTS_PATH="${POLYSIGHT_WEIGHTS_PATH:-}"

export POLYSIGHT_CLUSTER_ROOT POLYSIGHT_STORAGE_ROOT POLYSIGHT_DATA_ARCHIVE
export POLYSIGHT_DATA_DIR POLYSIGHT_MANIFEST_DIR POLYSIGHT_MLFLOW_ROOT
export POLYSIGHT_RUNS_DIR POLYSIGHT_WEIGHTS_PATH

cd "${POLYSIGHT_CLUSTER_ROOT}"
if [[ -f .venv-cluster/bin/activate ]]; then
  source .venv-cluster/bin/activate
fi

python --version
echo "Commit: $(git rev-parse HEAD)"
echo "Módulos: ${LOADEDMODULES:-unknown}"

start_mlflow_server() {
  local port="${POLYSIGHT_MLFLOW_PORT:-$((5000 + SLURM_JOB_ID % 1000))}"
  local database="${POLYSIGHT_MLFLOW_ROOT}/mlflow.db"
  local artifact_root="${POLYSIGHT_MLFLOW_ROOT}/artifacts"
  local server_log="${POLYSIGHT_MLFLOW_ROOT}/mlflow-server-${SLURM_JOB_ID}.log"
  mkdir -p "${POLYSIGHT_MLFLOW_ROOT}" "${artifact_root}"

  mlflow server \
    --backend-store-uri "sqlite:///${database}" \
    --artifacts-destination "${artifact_root}" \
    --serve-artifacts \
    --host 127.0.0.1 \
    --port "${port}" \
    >"${server_log}" 2>&1 &
  MLFLOW_SERVER_PID=$!
  export MLFLOW_SERVER_PID
  trap 'kill "${MLFLOW_SERVER_PID}" 2>/dev/null || true' EXIT

  POLYSIGHT_TRACKING_URI="http://127.0.0.1:${port}"
  export POLYSIGHT_TRACKING_URI
  for attempt in $(seq 1 30); do
    if python - <<'PY'
import os
import sys
import urllib.request

url = os.environ["POLYSIGHT_TRACKING_URI"] + "/health"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    with opener.open(url, timeout=2) as response:
        print(f"MLflow health check: HTTP {response.status}")
except Exception as exc:
    print(
        f"MLflow health check falló: {type(exc).__name__}: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(1)
PY
    then
      echo "MLflow disponible en ${POLYSIGHT_TRACKING_URI}"
      return 0
    fi
    if ! kill -0 "${MLFLOW_SERVER_PID}" 2>/dev/null; then
      echo "ERROR: el proceso de MLflow terminó durante el arranque." >&2
      tail -n 50 "${server_log}" >&2 || true
      return 1
    fi
    echo "MLflow aún no responde (intento ${attempt}/30); reintentando..." >&2
    sleep 1
  done
  echo "ERROR: MLflow no inició; revisar ${server_log}" >&2
  tail -n 50 "${server_log}" >&2 || true
  return 1
}
