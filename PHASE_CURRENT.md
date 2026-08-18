# PHASE_CURRENT

## Fase 8 — Reproducción verificable del experimento en Google Colab

**Objetivo:** Proporcionar notebooks que permitan verificar el modelo final y repetir
el entrenamiento `main16-baseline` con semilla 42 en Google Colab reutilizando el
pipeline versionado de PolySight.

**Contexto:** Ver `docs/training-protocol.md`, `docs/traceability.md`,
`configs/main16-baseline.yaml` y `experiments/final-evaluation.yaml`.

---

### Tareas

- [~] Crear notebook de verificación por inferencia con checkpoint auditado
- [ ] Crear notebook de reproducción de entrenamiento `main16-baseline`, semilla 42
- [ ] Verificar entorno, dataset, manifest, pesos iniciales y trazabilidad de versiones
- [ ] Agregar validaciones automáticas de estructura y sintaxis de los notebooks
- [ ] Documentar uso, limitaciones y diferencia entre reproducción metodológica y binaria
- [ ] Ejecutar pruebas y Ruff, cerrar la fase e integrar en `dev`

---

### Notas y decisiones

- Los notebooks orquestan el paquete y sus comandos; no duplican las implementaciones
  de `src/polysight/` en celdas.
- La reproducción principal se limita a `main16-baseline` con semilla 42. Repetir los
  nueve runs históricos queda fuera del alcance inicial.
- La evaluación sobre test permanecerá desactivada por defecto en el notebook de
  entrenamiento y solo debe habilitarse una vez, sin ajustar el modelo después.
- El resultado esperado es paridad de protocolo y métricas comparables; no identidad
  binaria entre checkpoints producidos por CEDIA y Colab.
