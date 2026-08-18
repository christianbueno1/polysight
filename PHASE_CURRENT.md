# PHASE_CURRENT

## Fase 9 — Release estable v0.1.1

**Objetivo:** Publicar en `main` las mejoras documentales y de reproducibilidad
acumuladas en `dev` después de `v0.1.0`, sin modificar los modelos auditados.

**Contexto:** Incluye las guías de API, segmentación y CEDIA, además de los notebooks
de verificación y reproducción en Google Colab.

---

### Tareas

- [~] Actualizar la versión del paquete a `0.1.1`
- [ ] Ejecutar pruebas, Ruff, build y verificaciones de notebooks
- [ ] Registrar el release en `CHANGELOG.md`
- [ ] Integrar el branch de release en `dev`
- [ ] Mergear `dev` en `main` con `--no-ff`
- [ ] Crear y publicar el tag anotado `v0.1.1`
- [ ] Confirmar sincronización de `dev`, `main` y el tag con `origin`

---

### Notas y decisiones

- `v0.1.1` es un release de documentación y reproducibilidad; no cambia checkpoints,
  entrenamiento, métricas oficiales ni artefactos auditados de `v0.1.0`.
- La ejecución completa de los notebooks en Colab permanece como validación externa,
  porque requiere GPU y archivos grandes que no forman parte del repositorio.
