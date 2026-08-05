# Registro de experimentos

Este directorio contiene metadatos pequeños y versionables de los experimentos.
Los modelos, logs completos y artefactos de MLflow permanecen fuera de Git.

## Estructura

- `runs/<slurm_job_id>.yaml`: ficha inmutable de un job de entrenamiento.
- `summary.csv`: índice regenerable para comparar runs.
- `final-evaluation.yaml`: selección final y única evaluación sobre test por perfil.

Las fichas separan tres conceptos:

1. `requested_resources`: recursos reservados por Slurm.
2. `observed_consumption`: consumo informado por el accounting de Slurm.
3. `point_samples`: observaciones manuales que no representan necesariamente un máximo.

## Fuentes autoritativas

| Dato | Fuente |
|---|---|
| Estado, duración, CPU, RAM y recursos asignados | `sacct` |
| Métricas de validation | `validation/metrics.json`, también registrado en MLflow |
| Run ID y artefactos | MLflow y directorio del run |
| Commit ejecutado | output de Slurm |
| Configuración y semilla | configuración YAML y parámetros del envío |
| Memoria GPU puntual | `nvidia-smi`, si se tomó una muestra durante el job |

`max_rss_mib` corresponde al step de entrenamiento (`<job>.0`). El consumo del proceso
batch, que hospeda MLflow, se registra por separado. `average_cpu_cores` se calcula como
`TotalCPU / elapsed` y expresa núcleos equivalentes ocupados durante el job.

Una muestra de memoria GPU nunca se interpreta como pico. Para obtener máximos reales,
el cluster tendría que publicar métricas GPU en Slurm o se tendría que activar muestreo
periódico dentro del job.

## Recolección

Después de que un job termine:

```bash
.venv/bin/python scripts/cluster/collect-experiment.py \
  --job-id 20755 \
  --run-id cb29daac69dd4c9aa8a31ca621d08613 \
  --config configs/main16-baseline.yaml \
  --seed 42 \
  --gpu-memory-sample-mib 7378 \
  --gpu-sample-note "nvidia-smi ejecutado mediante srun durante el entrenamiento"
```

El recolector consulta CEDIA por SSH, crea la ficha YAML y regenera `summary.csv`. Se
niega a sobrescribir una ficha existente, salvo que se use explícitamente `--force`.
