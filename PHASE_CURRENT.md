# PHASE_CURRENT

## Fase 1 — Estructura, gobierno y entorno local del proyecto

**Objetivo:** Establecer la estructura instalable, las convenciones y la documentación
necesarias para desarrollar el pipeline sin incluir datos ni ejecutar entrenamiento local.

---

### Tareas

- [x] Inicializar `dev` y crear el branch `chore/estructura-proyecto`
- [x] Crear `BACKLOG.md` antes de los demás archivos de orquestación
- [x] Crear `PHASE_CURRENT.md` y `CHANGELOG.md`
- [x] Reemplazar el `.gitignore` genérico por reglas específicas del proyecto
- [x] Crear el paquete instalable y declarar dependencias sin reinstalar PyTorch
- [x] Documentar arquitectura, flujo local/cluster y comandos previstos

---

### Notas y decisiones

- La rama `dev` contiene el commit raíz porque `main` queda reservada para releases.
- PyTorch no se declara como dependencia de `pip`; CEDIA proporcionará `pytorch/2.2`.
- Los nombres de código y configuración se escriben en inglés; la documentación, en español.
- Dataset, checkpoints, runs MLflow, logs y credenciales se excluyen de Git.
