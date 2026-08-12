# Auditoría de trazabilidad experimental

**Estado:** verificada el 2026-08-12 16:35 -0500.

La auditoría recorre la cadena completa desde los resultados finales hasta el código y
los datos que los produjeron:

```text
resultado test
  -> job de evaluación
  -> checkpoint seleccionado
  -> run MLflow y job de entrenamiento
  -> configuración efectiva
  -> manifest
  -> commit de código
```

## Modelos finales

| Perfil | Estrategia y semilla | Job entrenamiento | Run MLflow | Commit entrenamiento | Job test oficial | Commit test | Job derivado |
|---|---|---:|---|---|---:|---|---:|
| `main16` | baseline, 42 | 20755 | `cb29daac69dd4c9aa8a31ca621d08613` | `87ac0694…` | 20769 | `fe8d0be9…` | 22953 |
| `full23` | baseline, 2026 | 20767 | `29029e09b7034dac8013b07c0897c6b4` | `0067f2d1…` | 20770 | `fe8d0be9…` | 22954 |

Los seis jobs de esta tabla terminaron `COMPLETED` con exit code `0:0`. Los jobs
derivados usaron el commit `8ee600d4990cd292cef5f693defdfb75d0b99fb5` y no
reemplazaron los resultados oficiales.

## Inputs congelados

| Perfil | Configuración SHA-256 | Manifest SHA-256 | Checkpoint SHA-256 |
|---|---|---|---|
| `main16` | `409c005fc28a240e71c53071dea23a49f425b1078df335582e5fdf3bcf3cf1c0` | `8f59d5c5f1d188ad75d1b28c6ab9b56e3b3c68bcf8f7dd0940422dc8df27f463` | `74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c` |
| `full23` | `36185fbdc25a44f829c04da6a46dbcd231523c453131ea0ed716fffa732a539a` | `baed4894f723c8be6446b05a02447534274c11d95aaa2d1fabef37a52cf402fd` | `4e5d588e2c1b556437a59c513d37e34ed108e4bced7f197bce704e22d77d5a67` |

La configuración `main16-weighted.yaml`, usada en los tres runs comparativos, tiene
SHA-256 `0c99152448ef1b4830d7f4528daa9a8f893204337dbd47006c1bcf93c418d81b`.

Las nueve configuraciones archivadas por MLflow son idénticas byte por byte a sus
archivos versionados. La semilla efectiva de cada run se conserva como parámetro
MLflow porque Slurm puede sobrescribir el valor base del YAML mediante `RUN_SEED`.

Los hashes de manifests son constantes entre las tres semillas y estrategias de cada
perfil. Los manifests no se sincronizan localmente; sus archivos reales fueron
verificados directamente en CEDIA y sus hashes coinciden con los tags de MLflow y con
`experiments/final-evaluation.yaml`.

## Runs y MLflow

Se verificaron los nueve runs de `experiments/summary.csv` contra:

- las nueve fichas `experiments/runs/<job>.yaml`;
- estado `FINISHED`, parámetros y tags de la SQLite de MLflow;
- configuración archivada dentro de cada run;
- `validation/metrics.json` y las cinco métricas del resumen;
- `validation/per-class-metrics.csv` y `validation/confusion-matrix.png`;
- `checkpoints/best.pt`;
- existencia de cada commit en el historial Git local.

La SQLite pasó `PRAGMA quick_check` y las 14 ubicaciones activas de experimentos y
runs usan el esquema portable `mlflow-artifacts:/`.

## Evaluación final y artefactos derivados

Para ambos perfiles se comprobó que:

- `metrics.json` oficial coincide con `test_metrics` de
  `experiments/final-evaluation.yaml`;
- los tres artefactos oficiales continúan presentes y sin modificación;
- `metrics.json` y `per-class-metrics.csv` derivados son idénticos byte por byte a
  los oficiales;
- los diez hashes de artefactos derivados coinciden con el manifiesto versionado;
- los checkpoints sincronizados desde MLflow tienen el mismo hash que los archivos
  usados en CEDIA;
- cada fila de `confusion-matrix.csv` suma su support y su diagonal reproduce el
  recall por clase.

Los hashes individuales y las rutas remotas están registrados en
`experiments/final-evaluation.yaml`.

## Repetir la auditoría local

La verificación requiere haber sincronizado `artifacts/cedia/mlflow/`,
`artifacts/cedia/final-evaluation/` y `artifacts/cedia/final-evaluation-derived/`:

```bash
uv run python scripts/audit-traceability.py
```

Una ejecución correcta informa:

```json
{
  "derived_artifacts": 10,
  "official_models": 2,
  "portable_mlflow_locations": 14,
  "sqlite_quick_check": "ok",
  "status": "ok",
  "training_runs": 9
}
```

## Límites de la auditoría

- Los artefactos binarios y datasets permanecen fuera de Git; su integridad depende de
  hashes y de la copia sincronizada desde CEDIA.
- Los logs y el accounting originales permanecen en CEDIA. La auditoría comprobó sus
  estados y commits, pero no los copia al repositorio.
- La trazabilidad demuestra procedencia e integridad de los archivos observados; no
  elimina las limitaciones estadísticas o clínicas descritas en `docs/results.md`.
