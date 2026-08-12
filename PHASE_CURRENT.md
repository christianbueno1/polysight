# PHASE_CURRENT

## Fase 7 — Legibilidad de matrices de confusión normalizadas

**Objetivo:** Mejorar la legibilidad de los heatmaps normalizados sin ejecutar de nuevo
entrenamiento o test y sin modificar los artefactos auditados del release `v0.1.0`.

**Contexto:** Ver `src/polysight/metrics.py`, `tests/test_metrics_artifacts.py`,
`artifacts/cedia/final-evaluation-derived/` y `docs/testing-summary.md`.

---

### Tareas

- [~] Ajustar tamaño, anotaciones, contraste y separación visual del heatmap normalizado
- [ ] Crear un comando reproducible para renderizar desde `confusion-matrix.csv`
- [ ] Agregar pruebas de formato, umbral y validación del CSV
- [ ] Generar e inspeccionar versiones legibles de `main16` y `full23`
- [ ] Actualizar documentación y validar pruebas, lint y trazabilidad

---

### Notas y decisiones

- Las matrices nuevas se derivan de los CSV de conteos ya verificados; no cargan
  checkpoints, datasets ni PyTorch.
- Los PNG auditados conservan sus nombres y hashes. Las versiones históricas mejoradas
  usarán el sufijo `confusion-matrix-normalized-readable.png`.
- La diagonal se anota siempre, incluidos valores 0%; errores fuera de la diagonal por
  debajo de 2% conservan el color pero omiten texto para reducir ruido.
- Los porcentajes usan formato compacto y el color de fuente se elige explícitamente
  según la intensidad de cada celda.
