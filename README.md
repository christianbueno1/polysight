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
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
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
