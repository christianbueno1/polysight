#!/usr/bin/env bash
#SBATCH --job-name=polysight-prepare
#SBATCH --partition=cpu-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail
source "${SLURM_SUBMIT_DIR}/slurm/common.sh"

DATASET_PARENT="${POLYSIGHT_STORAGE_ROOT}/datasets/hyper-kvasir"
mkdir -p "${DATASET_PARENT}" "${POLYSIGHT_MANIFEST_DIR}"

polysight-prepare --archive "${POLYSIGHT_DATA_ARCHIVE}" --output-dir "${DATASET_PARENT}"
polysight-split \
  --data-dir "${DATASET_PARENT}" \
  --output-dir "${POLYSIGHT_MANIFEST_DIR}" \
  --profile main16
polysight-split \
  --data-dir "${DATASET_PARENT}" \
  --output-dir "${POLYSIGHT_MANIFEST_DIR}" \
  --profile full23
