# PHASE_CURRENT

## Fase 9 — Release estable v0.1.1

**Objetivo:** Publicar en `main` las mejoras documentales y de reproducibilidad
acumuladas en `dev` después de `v0.1.0`, sin modificar los modelos auditados.

**Contexto:** Incluye las guías de API, segmentación y CEDIA, además de los notebooks
de verificación y reproducción en Google Colab.

---

### Tareas

- [x] Actualizar la versión del paquete a `0.1.1`
- [x] Ejecutar pruebas, Ruff, build y verificaciones de notebooks
- [x] Registrar el release en `CHANGELOG.md`
- [x] Integrar el branch de release en `dev`
- [x] Mergear `dev` en `main` con `--no-ff`
- [x] Crear y publicar el tag anotado `v0.1.1`
- [x] Confirmar sincronización de `dev`, `main` y el tag con `origin`

---

### Notas y decisiones

- `v0.1.1` es un release de documentación y reproducibilidad; no cambia checkpoints,
  entrenamiento, métricas oficiales ni artefactos auditados de `v0.1.0`.
- La ejecución completa de los notebooks en Colab permanece como validación externa,
  porque requiere GPU y archivos grandes que no forman parte del repositorio.
- La validación local pasó 23 pruebas, con una prueba omitida por ausencia local de
  PyTorch; Ruff y la auditoría de trazabilidad terminaron sin errores.
- Se construyeron correctamente `polysight-0.1.1.tar.gz` y
  `polysight-0.1.1-py3-none-any.whl`; los artefactos de build permanecen fuera de Git.
