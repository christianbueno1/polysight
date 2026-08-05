#!/usr/bin/env bash
#SBATCH --job-name=polysight-evaluate
#SBATCH --partition=gpu-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail
source "${SLURM_SUBMIT_DIR}/slurm/common.sh"

: "${CONFIG_PATH:?Debe exportar CONFIG_PATH}"
: "${CHECKPOINT_PATH:?Debe exportar CHECKPOINT_PATH}"
EVALUATION_DIR="${EVALUATION_DIR:-${POLYSIGHT_RUNS_DIR}/final-evaluation}"

srun polysight-evaluate \
  --config "${CONFIG_PATH}" \
  --checkpoint "${CHECKPOINT_PATH}" \
  --split test \
  --output-dir "${EVALUATION_DIR}"
