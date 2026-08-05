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
- [x] Hacer observable y robusto el health check local de MLflow
- [x] Consolidar por run métricas, procedencia y consumo computacional
- [x] Ejecutar baseline y weighted de `main16` con tres semillas
- [x] Elegir estrategia mediante macro-F1 de validation
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
- El baseline `main16`, semilla 42, terminó correctamente como job `20755` en 16:40,
  con macro-F1 de validation 0.858395.
- El health check de MLflow ignora proxies y conserva el error de cada intento; si el
  servidor termina o agota el plazo, adjunta el final de su log al output de Slurm.
- Los registros versionados viven en `experiments/runs/`; `summary.csv` permite comparar
  runs y el recolector conserva fuentes, recursos solicitados y consumo observado.
- Cadena `main16` restante: baseline 123 `20759`, baseline 2026 `20760`, weighted 42
  `20761`, weighted 123 `20762` y weighted 2026 `20763`, enlazados mediante `afterok`.
- El job `20759` inició correctamente sobre A100, creó su primer checkpoint y mostró
  5370 MiB de memoria GPU en una muestra puntual.
- Los jobs `20759`–`20763` terminaron `COMPLETED` con exit code `0:0`; sus fichas están
  consolidadas junto con `20755` en `experiments/`.
- Baseline gana para `full23`: macro-F1 medio 0.856086 (desviación 0.002987), frente a
  weighted 0.849512 (desviación 0.010611), calculado sobre semillas 42, 123 y 2026.
