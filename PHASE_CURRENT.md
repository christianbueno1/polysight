# PHASE_CURRENT

## Fase 3 — Pipeline PyTorch de entrenamiento y evaluación

**Objetivo:** Implementar EfficientNet-B0, carga de datos, entrenamiento en dos etapas,
evaluación, predicción y registro MLflow sin ejecutar entrenamiento local.

---

### Tareas

- [ ] Definir configuración tipada y archivos YAML experimentales
- [ ] Implementar Dataset, transforms y DataLoaders
- [ ] Implementar EfficientNet-B0 con cabeza configurable
- [ ] Implementar cross-entropy normal y ponderada
- [ ] Implementar entrenamiento AMP, early stopping, scheduler y reanudación
- [ ] Implementar evaluación y artefactos por clase
- [ ] Implementar predicción top-1/top-3
- [ ] Integrar MLflow y metadatos reproducibles
- [ ] Crear pruebas sin ciclos de optimización locales

---

### Notas y decisiones

- El entrenamiento real y el smoke test de una época se ejecutarán mediante Slurm.
- Localmente solo se validan interfaces, tensores y cálculos deterministas.
