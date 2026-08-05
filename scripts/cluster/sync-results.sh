#!/usr/bin/env bash
set -euo pipefail

REMOTE_MLFLOW="${1:-/home/christian.bueno__espol.edu.ec/projects/polysight-storage/mlflow}"
LOCAL_MLFLOW="${2:-artifacts/cedia/mlflow}"
INCOMING_DB="${LOCAL_MLFLOW}/.mlflow.db.incoming"
LOCK_DIR="${LOCAL_MLFLOW}/.sync.lock"

mkdir -p "${LOCAL_MLFLOW}/artifacts"
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  echo "ERROR: ya existe una sincronización activa en ${LOCAL_MLFLOW}" >&2
  exit 2
fi
cleanup() {
  rm -f "${INCOMING_DB}"
  rmdir "${LOCK_DIR}" 2>/dev/null || true
}
trap cleanup EXIT

rsync --archive --partial --info=progress2 \
  --exclude='*.log' \
  "cedia:${REMOTE_MLFLOW}/mlflow.db" "${INCOMING_DB}"

PYTHON_BIN="${POLYSIGHT_LOCAL_PYTHON:-.venv/bin/python}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi
"${PYTHON_BIN}" - "${INCOMING_DB}" <<'PY'
import sqlite3
import sys

database = sys.argv[1]
connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
if quick_check != "ok":
    raise SystemExit(f"Base MLflow inválida: {quick_check}")
locations = [
    row[0]
    for query in (
        "SELECT artifact_location FROM experiments",
        "SELECT artifact_uri FROM runs",
    )
    for row in connection.execute(query)
    if row[0]
]
invalid = [location for location in locations if not location.startswith("mlflow-artifacts:/")]
if invalid:
    raise SystemExit(f"MLflow contiene URI no portables: {invalid[:3]}")
print(f"Base MLflow válida; URI portables verificadas: {len(locations)}")
PY

rsync --archive --partial --info=progress2 \
  --exclude='*.log' \
  "cedia:${REMOTE_MLFLOW}/artifacts/" "${LOCAL_MLFLOW}/artifacts/"
mv "${INCOMING_DB}" "${LOCAL_MLFLOW}/mlflow.db"

echo "Abrir desde ${LOCAL_MLFLOW} con:"
echo "cd ${LOCAL_MLFLOW}"
echo "uvx mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --port 5000"
