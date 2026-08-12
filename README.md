# PolySight

Pipeline reproducible para clasificar hallazgos gastrointestinales de HyperKvasir
con transfer learning sobre EfficientNet-B0 y PyTorch.

## Alcance

- `main16`: experimento principal con las 16 clases que tienen al menos 100 imágenes.
- `full23`: experimento exploratorio con las 23 clases originales.
- Desarrollo y análisis local, sin entrenamiento.
- Entrenamiento en nodos GPU de CEDIA mediante Slurm.
- Seguimiento con MLflow en el cluster y sincronización para consulta local.

SUN-SEG no forma parte de este proyecto de clasificación.

## Inicio rápido

```bash
# despues de clonar el repositorio
cd ~/polysight

# Crear entorno virtual y activar

# usando venv + pip
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest

# usando uv project & package manager
uv sync --extra dev
uv run pytest
```

PyTorch debe instalarse por separado en local si se quieren ejecutar las pruebas que
lo requieren. En CEDIA se carga mediante `module load pytorch/2.2 cuda/12.4`.

Los comandos del pipeline son:

```bash
polysight-prepare --archive /ruta/hyper-kvasir-labeled-images.zip --output-dir data/hyper-kvasir
polysight-split --data-dir data/hyper-kvasir --output-dir manifests --profile main16
polysight-train --config configs/main16-baseline.yaml
polysight-evaluate --config configs/main16-baseline.yaml --checkpoint /ruta/best.pt --split test
polysight-predict --checkpoint /ruta/best.pt --image /ruta/imagen.jpg
```

Consulta [la guía de CEDIA](docs/cluster.md) para el entorno remoto y
[la ficha del dataset](docs/datasets/hyper-kvasir.md) para su ubicación y hash.

## Reproducir `main16` en CEDIA

Cada integrante debe clonar el repositorio en su propia cuenta de CEDIA. Desde el nodo
de acceso, reemplazar la URL y las rutas según corresponda:

```bash
ssh USUARIO@hpc.cedia.edu.ec
mkdir -p "$HOME/projects"
git clone git@github.com:ORGANIZACION/polysight.git "$HOME/projects/polysight"
cd "$HOME/projects/polysight"
git checkout dev
```

Para una reproducción exacta se debe registrar el commit ejecutado con
`git rev-parse HEAD` y mantenerlo sin cambios durante los seis entrenamientos. El
dataset `hyper-kvasir-labeled-images.zip` no está versionado en Git; debe copiarse al
clúster y comprobarse contra el hash documentado en
[la ficha de HyperKvasir](docs/datasets/hyper-kvasir.md).
El dataset lo puedes copiar en el cluster a este directorio: `$HOME/datasets/hyper-kvasir-labeled-images.zip`. El pipeline de preparación y splits genera los manifiestos de entrenamiento, validación y test en
`manifests/main16` y `manifests/full23`.

Las rutas predeterminadas de los jobs corresponden a la cuenta original. En otra
cuenta se exportan rutas propias al enviar cada job:

```bash
export POLYSIGHT_CLUSTER_ROOT="$HOME/projects/polysight"
export POLYSIGHT_STORAGE_ROOT="$HOME/projects/polysight-storage"
export POLYSIGHT_DATA_ARCHIVE="$HOME/datasets/hyper-kvasir-labeled-images.zip"
cd "$POLYSIGHT_CLUSTER_ROOT"

sbatch --export=ALL slurm/bootstrap.sbatch
```

Después de que termine `bootstrap`, validar el entorno y preparar el dataset. Los jobs
se ejecutan mediante Slurm; el nodo de acceso se usa solamente para Git, transferencia
de archivos y comandos administrativos como `sbatch`, `squeue` y `sacct`.

```bash
sbatch --export=ALL slurm/diagnose.sbatch
sbatch --export=ALL slurm/prepare-data.sbatch
sbatch --export=ALL slurm/smoke.sbatch
```

Revisar que cada job termine con estado `COMPLETED` y código `0:0` antes de continuar:

```bash
squeue -u "$USER"
sacct -j JOB_ID --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS
tail -n 100 slurm-polysight-NOMBRE-JOB_ID.out
```

### Protocolo experimental de `main16`

El experimento compara `configs/main16-baseline.yaml` y
`configs/main16-weighted.yaml` con las mismas semillas: `42`, `123` y `2026`. Los seis
jobs deben encadenarse con dependencias `afterok` para evitar escrituras concurrentes
en `mlflow.db`. Cada asignación captura automáticamente el ID que imprime `sbatch`:

```bash
JOB_BASELINE_42=$(sbatch --parsable --export=ALL,CONFIG_PATH=configs/main16-baseline.yaml,RUN_SEED=42 slurm/train.sbatch)
JOB_BASELINE_123=$(sbatch --parsable --dependency="afterok:${JOB_BASELINE_42}" --export=ALL,CONFIG_PATH=configs/main16-baseline.yaml,RUN_SEED=123 slurm/train.sbatch)
JOB_BASELINE_2026=$(sbatch --parsable --dependency="afterok:${JOB_BASELINE_123}" --export=ALL,CONFIG_PATH=configs/main16-baseline.yaml,RUN_SEED=2026 slurm/train.sbatch)
JOB_WEIGHTED_42=$(sbatch --parsable --dependency="afterok:${JOB_BASELINE_2026}" --export=ALL,CONFIG_PATH=configs/main16-weighted.yaml,RUN_SEED=42 slurm/train.sbatch)
JOB_WEIGHTED_123=$(sbatch --parsable --dependency="afterok:${JOB_WEIGHTED_42}" --export=ALL,CONFIG_PATH=configs/main16-weighted.yaml,RUN_SEED=123 slurm/train.sbatch)
JOB_WEIGHTED_2026=$(sbatch --parsable --dependency="afterok:${JOB_WEIGHTED_123}" --export=ALL,CONFIG_PATH=configs/main16-weighted.yaml,RUN_SEED=2026 slurm/train.sbatch)
printf '%s\n' "$JOB_BASELINE_42" "$JOB_BASELINE_123" "$JOB_BASELINE_2026" "$JOB_WEIGHTED_42" "$JOB_WEIGHTED_123" "$JOB_WEIGHTED_2026"
```

La estrategia se elige por el mayor **macro-F1 promedio de validation** entre sus tres
semillas; no por el mejor run individual. Dentro de la estrategia ganadora se escoge
el checkpoint con mayor macro-F1 de validation. Solo entonces se evalúa ese checkpoint
una vez sobre `test`, sin ajustar el modelo a partir del resultado:

```bash
sbatch --export=ALL,CONFIG_PATH=configs/main16-baseline.yaml,CHECKPOINT_PATH=/ruta/al/best.pt,EVALUATION_DIR="$POLYSIGHT_STORAGE_ROOT/runs/final-evaluation/main16" slurm/evaluate.sbatch
```

Los parámetros, métricas esperadas y procedencia de la ejecución original están en
`experiments/summary.csv`, `experiments/final-evaluation.yaml` y
[los resultados documentados](docs/results.md).

MLflow usa SQLite y artefactos portables: se sincronizan `mlflow.db` y `artifacts/`,
sin reescribir URI ni copiar logs del servidor.
