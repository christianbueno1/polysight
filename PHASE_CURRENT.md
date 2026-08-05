# PHASE_CURRENT

## Fase 5 — Ejecución experimental main16 y full23

**Objetivo:** Publicar el código trazable, validar el entorno CEDIA y ejecutar los
experimentos acordados sin utilizar el nodo de login para cómputo.

---

### Tareas

- [x] Reautenticar `gh` y crear el repositorio privado de GitHub
- [x] Publicar `main` y `dev`; configurar `dev` como branch de trabajo
- [x] Configurar acceso GitHub desde CEDIA y clonar el repositorio
- [x] Ejecutar bootstrap y diagnóstico en nodos Slurm
- [x] Preparar el dataset remoto y verificar los manifests
- [x] Ejecutar el smoke test de una época
- [ ] Ejecutar baseline y weighted de `main16` con tres semillas
- [ ] Elegir estrategia mediante macro-F1 de validation
- [ ] Ejecutar `full23` con la estrategia ganadora y tres semillas
- [ ] Evaluar una vez los modelos finales sobre test
- [x] Sincronizar MLflow portable y comprobar la UI local

---

### Notas y decisiones

- Repositorio privado: `christianbueno1/polysight`.
- CEDIA usa su clave dedicada mediante OpenSSH; `gh` no es necesario en el cluster.
- El clon vive en `~/projects/polysight` y los datos originales en `~/datasets`.
- Jobs completados: bootstrap `20735`, diagnóstico GPU `20736`, datos `20737`,
  smoke inicial `20738` y smoke portable `20739`.
- El módulo `pytorch/2.2` expone realmente torch 2.10.0+cu128 y torchvision 0.25.0+cu128.
- MLflow usa SQLite + `mlflow-artifacts:/`; no se reescriben rutas después de sincronizar.
- La copia local de `mlflow.db` y `artifacts/` fue validada y la UI inició correctamente.
- No hay jobs activos. El siguiente paso es enviar secuencialmente los seis runs de `main16`.
