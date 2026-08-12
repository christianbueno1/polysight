#!/usr/bin/env bash
set -euo pipefail

: "${1:?Uso: $0 slurm/job.sbatch [VARIABLE=valor ...]}"
JOB_PATH="$1"
shift
REMOTE_DIR="${POLYSIGHT_REMOTE_DIR:-/home/christian.bueno__espol.edu.ec/projects/polysight}"

EXPORTS="ALL"
for assignment in "$@"; do
  if [[ ! "${assignment}" =~ ^[A-Z_][A-Z0-9_]*=[A-Za-z0-9_./:-]+$ ]]; then
    echo "Asignación inválida: ${assignment}" >&2
    exit 2
  fi
  EXPORTS+=",${assignment}"
done

ssh cedia "cd '${REMOTE_DIR}' && sbatch --export='${EXPORTS}' '${JOB_PATH}'"
