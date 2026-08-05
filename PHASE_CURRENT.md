# PHASE_CURRENT

## Fase 2 — Preparación reproducible de HyperKvasir y splits

**Objetivo:** Validar el archivo oficial, extraerlo de forma segura y generar manifests
deterministas para los perfiles `main16` y `full23` sin versionar imágenes.

---

### Tareas

- [ ] Implementar validación de tamaño, SHA-256, estructura y conteos
- [ ] Implementar extracción segura e idempotente
- [ ] Implementar perfiles `main16` y `full23`
- [ ] Generar splits 70/15/15 por clase con hashes y semilla fija
- [ ] Mantener duplicados exactos en un mismo split
- [ ] Generar reporte de posibles duplicados perceptuales
- [ ] Crear pruebas unitarias del pipeline de datos
- [ ] Actualizar la documentación del dataset

---

### Notas y decisiones

- El perfil principal aplica el umbral reproducible de 100 imágenes por clase.
- `full23` reserva al menos un ejemplo de cada clase para validation y test.
- La ausencia de identificadores de paciente/procedimiento se documenta como limitación.
