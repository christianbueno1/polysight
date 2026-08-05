# PHASE_CURRENT

## Fase 4 — Integración con CEDIA, Slurm y sincronización MLflow

**Objetivo:** Proporcionar jobs seguros para diagnóstico, preparación y entrenamiento
en nodos de cómputo, junto con sincronización reproducible por Git y rsync.

---

### Tareas

- [x] Implementar bootstrap del entorno remoto reutilizando módulos
- [x] Crear job diagnóstico de GPU y dependencias
- [x] Crear job CPU de preparación del dataset
- [x] Crear job GPU de smoke test
- [x] Crear job GPU parametrizable de entrenamiento
- [x] Crear job de evaluación de test
- [x] Crear scripts de envío y sincronización de datos/resultados
- [x] Hacer portables los URI de artefactos MLflow sincronizados
- [x] Documentar la operación sin ejecutar cargas en `login1`

---

### Notas y decisiones

- Todos los accesos usan `ssh cedia`, que respeta `~/.ssh/config`.
- El perfil inicial solicita una A100 de 40 GB en `gpu-dev`; no usa multi-GPU.
