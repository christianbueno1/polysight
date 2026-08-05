# PHASE_CURRENT

## Fase 3 — Pipeline PyTorch de entrenamiento y evaluación

**Objetivo:** Implementar EfficientNet-B0, carga de datos, entrenamiento en dos etapas,
evaluación, predicción y registro MLflow sin ejecutar entrenamiento local.

---

### Tareas

- [x] Definir configuración tipada y archivos YAML experimentales
- [x] Implementar Dataset, transforms y DataLoaders
- [x] Implementar EfficientNet-B0 con cabeza configurable
- [x] Implementar cross-entropy normal y ponderada
- [x] Implementar entrenamiento AMP, early stopping, scheduler y reanudación
- [x] Implementar evaluación y artefactos por clase
- [x] Implementar predicción top-1/top-3
- [x] Integrar MLflow y metadatos reproducibles
- [x] Crear pruebas sin ciclos de optimización locales

---

### Notas y decisiones

- El entrenamiento real y el smoke test de una época se ejecutarán mediante Slurm.
- Localmente solo se validan interfaces, tensores y cálculos deterministas.
- Las pruebas que importan PyTorch se omiten localmente y se ejecutarán en el diagnóstico CEDIA.
