#!/usr/bin/env bash
set -euo pipefail

REMOTE_STORAGE="${1:-/home/christian.bueno__espol.edu.ec/polysight-storage}"
LOCAL_STORAGE="${2:-artifacts/cedia}"

mkdir -p "${LOCAL_STORAGE}/mlruns" "${LOCAL_STORAGE}/runs"
rsync --archive --partial --info=progress2 \
  "cedia:${REMOTE_STORAGE}/mlruns/" "${LOCAL_STORAGE}/mlruns/"
rsync --archive --partial --info=progress2 \
  "cedia:${REMOTE_STORAGE}/runs/" "${LOCAL_STORAGE}/runs/"

.venv/bin/python scripts/rebase-mlflow.py \
  --mlruns-dir "${LOCAL_STORAGE}/mlruns" \
  --remote-root "${REMOTE_STORAGE}"

echo "Abrir con: mlflow ui --backend-store-uri ${LOCAL_STORAGE}/mlruns"
