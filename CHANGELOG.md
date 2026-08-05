# CHANGELOG

---

## 2026-08-04 21:27 -0500 — Fase 2: preparación de HyperKvasir

**Hecho:**
- Implementadas la verificación integral y la extracción segura e idempotente del ZIP.
- Implementados manifests deterministas 70/15/15 para `main16` y `full23`.
- Incorporados hashes exactos, agrupación de duplicados y reporte perceptual dHash.
- Añadidas pruebas del archivo, perfiles, splits, duplicados y metadatos.

**Decisiones:**
- Las clases de `main16` se derivan del umbral de 100 imágenes, no de una lista manual.
- Los duplicados con etiquetas contradictorias detienen la preparación.
- La similitud perceptual solo produce un reporte porque no demuestra identidad clínica.

**Pendiente / carry-over:**
- Ejecutar el pipeline real después de que el entorno local `uv` esté disponible.
- Implementar entrenamiento, evaluación y predicción PyTorch.

---

## 2026-08-04 21:09 -0500 — Fase 1: estructura y gobierno

**Hecho:**
- Registrado el contexto inicial en `dev` y creado el branch de la primera fase.
- Definido el backlog de seis fases y la estructura instalable del proyecto.
- Configurado Git para excluir datasets, modelos, resultados y secretos.

**Decisiones:**
- `main` se mantiene sin trabajo directo y se creará al producir el primer release estable.
- Las dependencias Python excluyen PyTorch para reutilizar el módulo optimizado de CEDIA.
- El desarrollo y las pruebas sin optimización ocurren localmente; el entrenamiento solo mediante Slurm.

**Pendiente / carry-over:**
- Preparar HyperKvasir y generar los manifests reproducibles de `main16` y `full23`.
