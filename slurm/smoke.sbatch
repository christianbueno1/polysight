#!/usr/bin/env bash
#SBATCH --job-name=polysight-smoke
#SBATCH --partition=gpu-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail
source "${SLURM_SUBMIT_DIR}/slurm/common.sh"
start_mlflow_server

nvidia-smi
srun polysight-train --config configs/smoke-main16.yaml --seed 42
