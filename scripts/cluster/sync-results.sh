#!/usr/bin/env bash
set -euo pipefail

REMOTE_MLFLOW="${1:-/home/christian.bueno__espol.edu.ec/projects/polysight-storage/mlflow}"
LOCAL_MLFLOW="${2:-artifacts/cedia/mlflow}"

mkdir -p "${LOCAL_MLFLOW}/artifacts"
rsync --archive --partial --info=progress2 \
  --exclude='*.log' \
  "cedia:${REMOTE_MLFLOW}/mlflow.db" "${LOCAL_MLFLOW}/mlflow.db"
rsync --archive --partial --info=progress2 \
  --exclude='*.log' \
  "cedia:${REMOTE_MLFLOW}/artifacts/" "${LOCAL_MLFLOW}/artifacts/"

echo "Abrir desde ${LOCAL_MLFLOW} con:"
echo "uvx mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --port 5000"
