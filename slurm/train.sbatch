#!/usr/bin/env bash
#SBATCH --job-name=polysight-train
#SBATCH --partition=gpu-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --time=04:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail
source "${SLURM_SUBMIT_DIR}/slurm/common.sh"

: "${CONFIG_PATH:?Debe exportar CONFIG_PATH, por ejemplo configs/main16-weighted.yaml}"
RUN_SEED="${RUN_SEED:-42}"
if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "ERROR: no existe CONFIG_PATH=${CONFIG_PATH}" >&2
  exit 2
fi

nvidia-smi
srun polysight-train --config "${CONFIG_PATH}" --seed "${RUN_SEED}"
