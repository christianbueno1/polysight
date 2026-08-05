# PHASE_CURRENT

## Fase 4 — Integración con CEDIA, Slurm y sincronización MLflow

**Objetivo:** Proporcionar jobs seguros para diagnóstico, preparación y entrenamiento
en nodos de cómputo, junto con sincronización reproducible por Git y rsync.

---

### Tareas

- [ ] Implementar bootstrap del entorno remoto reutilizando módulos
- [ ] Crear job diagnóstico de GPU y dependencias
- [ ] Crear job CPU de preparación del dataset
- [ ] Crear job GPU de smoke test
- [ ] Crear job GPU parametrizable de entrenamiento
- [ ] Crear job de evaluación de test
- [ ] Crear scripts de envío y sincronización de datos/resultados
- [ ] Hacer portables los URI de artefactos MLflow sincronizados
- [ ] Documentar la operación sin ejecutar cargas en `login1`

---

### Notas y decisiones

- Todos los accesos usan `ssh cedia`, que respeta `~/.ssh/config`.
- El perfil inicial solicita una A100 de 40 GB en `gpu-dev`; no usa multi-GPU.
