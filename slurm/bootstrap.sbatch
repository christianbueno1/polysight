#!/usr/bin/env bash
#SBATCH --job-name=polysight-bootstrap
#SBATCH --partition=cpu-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail
if [[ -z "${SLURM_JOB_ID:-}" ]] || [[ "$(hostname)" == login* ]]; then
  echo "ERROR: bootstrap debe ejecutarse mediante Slurm." >&2
  exit 2
fi

module purge
module load pytorch/2.2
module load cuda/12.4

REQUIRED_PYTHON="3.11"
FOUND_PYTHON="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if [[ "${FOUND_PYTHON}" != "${REQUIRED_PYTHON}" ]]; then
  echo "ERROR: se requiere Python ${REQUIRED_PYTHON} (pyproject.toml: requires-python==3.11.*)." >&2
  echo "       el modulo pytorch/2.2 expuso Python ${FOUND_PYTHON} en su lugar." >&2
  echo "       binario resuelto: $(command -v python)" >&2
  exit 3
fi
echo "Python ${FOUND_PYTHON} verificado ($(command -v python))."

cd "${POLYSIGHT_CLUSTER_ROOT:-${SLURM_SUBMIT_DIR}}"

python -m venv --system-site-packages .venv-cluster
source .venv-cluster/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

python -c 'import torch; print("torch", torch.__version__)'
echo "Entorno del cluster preparado."