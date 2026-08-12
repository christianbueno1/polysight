#!/usr/bin/env bash
#SBATCH --job-name=polysight-diagnose
#SBATCH --partition=gpu-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --gres=gpu:a100-sxm4-40gb:1
#SBATCH --time=00:15:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail
source "${SLURM_SUBMIT_DIR}/slurm/common.sh"

nvidia-smi
python - <<'PY'
import json
import torch
import torchvision

report = {
    "torch": torch.__version__,
    "torchvision": torchvision.__version__,
    "cuda_build": torch.version.cuda,
    "cuda_available": torch.cuda.is_available(),
    "cudnn": torch.backends.cudnn.version(),
    "device_count": torch.cuda.device_count(),
    "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
print(json.dumps(report, indent=2))
if not report["cuda_available"]:
    raise SystemExit("CUDA no está disponible")
PY

python -m pytest -q
python -m ruff check .
