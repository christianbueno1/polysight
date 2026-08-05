# PHASE_CURRENT

## Fase 5 — Ejecución experimental main16 y full23

**Objetivo:** Publicar el código trazable, validar el entorno CEDIA y ejecutar los
experimentos acordados sin utilizar el nodo de login para cómputo.

---

### Tareas

- [ ] Reautenticar `gh` y crear el repositorio privado de GitHub
- [ ] Publicar `main` y `dev`; configurar `dev` como branch de trabajo
- [ ] Configurar acceso GitHub desde CEDIA y clonar el repositorio
- [ ] Ejecutar bootstrap y diagnóstico en nodos Slurm
- [ ] Preparar el dataset remoto y verificar los manifests
- [ ] Ejecutar el smoke test de una época
- [ ] Ejecutar baseline y weighted de `main16` con tres semillas
- [ ] Elegir estrategia mediante macro-F1 de validation
- [ ] Ejecutar `full23` con la estrategia ganadora y tres semillas
- [ ] Evaluar una vez los modelos finales sobre test
- [ ] Sincronizar runs y comprobar MLflow local

---

### Notas y decisiones

- La fase está bloqueada hasta renovar la autenticación de GitHub.
- No se sustituirá Git por una copia ad hoc para evitar perder trazabilidad experimental.
