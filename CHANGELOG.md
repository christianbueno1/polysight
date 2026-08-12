# CHANGELOG

---

## 2026-08-12 16:21 -0500 — Fase 6: matrices finales crudas y normalizadas

**Hecho:**
- Ejecutados en CEDIA los jobs `22953` (`main16`) y `22954` (`full23`) con los
  checkpoints y manifests finales congelados.
- Verificada la coincidencia byte por byte de métricas agregadas y por clase respecto
  de los artefactos oficiales.
- Sincronizados los conteos crudos y heatmaps normalizados bajo
  `artifacts/cedia/final-evaluation-derived/` y registrada su procedencia y hashes.

**Decisiones:**
- La regeneración se almacena separada y no reemplaza los jobs oficiales `20769` y
  `20770` ni habilita ajustes de modelos o hiperparámetros.
- Los artefactos derivados se aceptan porque cada fila del CSV suma su support, la
  diagonal reproduce el recall y las métricas son idénticas a las originales.

**Pendiente / carry-over:**
- Continuar con la verificación completa de trazabilidad del release.

---

## 2026-08-12 16:00 -0500 — Fase 6: documentación del protocolo de entrenamiento

**Hecho:**
- Creado `docs/training-protocol.md` con la explicación de las semillas, pesos
  iniciales, entrenamiento en dos etapas, early stopping y épocas ejecutadas.
- Aclarado que la mejora de matrices no requiere repetir entrenamientos ni reabrir
  test.

**Decisiones:**
- Los valores de semilla se presentan como estados pseudoaleatorios arbitrarios, no
  como números con una ventaja científica intrínseca.
- Los límites de épocas y paciencia se documentan como heurísticas fijas porque no se
  realizó una búsqueda sistemática que demostrara su optimalidad.

**Pendiente / carry-over:**
- Completar la trazabilidad, validación final y preparación del release.

---

## 2026-08-12 13:23 -0500 — Fase 6: matrices de confusión auditables

**Hecho:**
- Extendido `save_evaluation_artifacts` para guardar conteos en
  `confusion-matrix.csv` y un heatmap normalizado por clase real.
- Añadidas pruebas de normalización, filas sin soporte, contenido del CSV y archivos
  generados.
- Actualizada la documentación para distinguir el formato nuevo de los artefactos
  finales históricos.

**Decisiones:**
- La visualización normalizada usa escala fija de 0% a 100% y omite anotaciones en
  celdas con valor cero.
- No se repiten las evaluaciones finales de test ni se reconstruyen matrices desde los
  PNG; la mejora aplica a validation y evaluaciones futuras.

**Pendiente / carry-over:**
- Verificar trazabilidad de configuraciones, commits, manifests y artefactos.

---

## 2026-08-12 12:54 -0500 — Fase 6: resumen didáctico de testing

**Hecho:**
- Creado `docs/testing-summary.md` con las métricas finales de `main16` y `full23`.
- Explicada la lectura de la matriz de confusión de `main16`, incluidas sus clases
  fuertes, confusiones relevantes y limitaciones visuales.

**Decisiones:**
- El resumen didáctico se mantiene separado de `docs/results.md`, que funciona como
  reporte formal del experimento.
- Las conclusiones cuantitativas se apoyan en `per-class-metrics.csv`; el heatmap se
  interpreta cualitativamente porque muestra conteos absolutos sin anotaciones.

**Pendiente / carry-over:**
- Continuar con la verificación de trazabilidad y la documentación del release.

---

## 2026-08-11 17:48 -0500 — Fase 6: guía de reproducción de main16 en CEDIA

**Hecho:**
- Documentado en el README el clonado del repositorio dentro de una cuenta de CEDIA.
- Añadidos los pasos de bootstrap, diagnóstico, preparación de datos y smoke test.
- Documentados los seis entrenamientos de main16 y su encadenamiento con `afterok`.
- Registrado el criterio de selección por macro-F1 promedio de validation y la política
  de una única evaluación final sobre test.

**Decisiones:**
- Cada integrante usa rutas bajo su propia cuenta mediante variables de entorno, sin
  depender de las rutas predeterminadas de la ejecución original.
- Los entrenamientos se ejecutan secuencialmente para evitar escrituras concurrentes
  sobre la base SQLite de MLflow.
- El commit se mantiene fijo durante los seis runs para conservar trazabilidad.

**Pendiente / carry-over:**
- Completar la documentación principal con el resumen final de resultados y verificar
  toda la trazabilidad del release.

---

## 2026-08-05 18:23 -0500 — Fase 6: conclusiones y amenazas a la validez

**Hecho:**
- Documentadas conclusiones de main16, weighted y full23 sin modificar modelos.
- Registradas amenazas internas, estadísticas, de constructo, medición y validez externa.
- Delimitadas explícitamente las afirmaciones permitidas por el experimento.

**Decisiones:**
- Main16 se describe como baseline reproducible en HyperKvasir, no como modelo validado
  clínicamente.
- Full23 se considera insuficiente para clasificación equilibrada de 23 clases bajo el
  protocolo actual, pese a su accuracy global.
- No se realizan nuevos ajustes derivados de resultados test.

**Pendiente / carry-over:**
- Verificar trazabilidad completa de configuraciones, commits, manifests y artefactos.

---

## 2026-08-05 18:15 -0500 — Fase 6: consumo y estabilidad

**Hecho:**
- Agregados tiempo A100, CPU efectiva, MaxRSS y épocas ejecutadas para nueve runs.
- Documentadas 2:01:11 de asignación A100, ~11.86 CPU-h y ~4.13 GiB de MaxRSS.
- Relacionadas las diferencias de duración con las épocas registradas en MLflow.

**Decisiones:**
- Las tres lecturas de memoria GPU se mantienen como muestras puntuales, no máximos.
- No se recomienda reducir recursos GPU sin telemetría de utilización y pico de memoria.
- Estabilidad se describe mediante desviación entre tres semillas, sin inferencia de
  significancia estadística.

**Pendiente / carry-over:**
- Documentar conclusiones, limitaciones y amenazas a la validez.

---

## 2026-08-05 18:14 -0500 — Fase 6: análisis por clase y matrices

**Hecho:**
- Analizadas métricas por clase y matrices finales de main16 y full23.
- Identificadas seis clases full23 con F1 cero y soportes entre 1 y 8 ejemplos.
- Documentadas las clases débiles y fuertes de main16 y los grupos de confusión visibles.

**Decisiones:**
- Las métricas por clase son la fuente cuantitativa; el heatmap solo permite lectura
  cualitativa de errores fuera de la diagonal.
- No se repite test para reconstruir conteos. Para futuras rondas se recomienda guardar
  matriz cruda CSV y visualización normalizada por fila desde la primera evaluación.

**Pendiente / carry-over:**
- Documentar rendimiento, estabilidad y consumo computacional.

---

## 2026-08-05 16:47 -0500 — Fase 6: comparación agregada de resultados

**Hecho:**
- Calculadas medias y desviaciones de cinco métricas sobre tres semillas para main16
  baseline, main16 weighted y full23 baseline.
- Documentados por separado validation y la única evaluación final sobre test.
- Cuantificadas las brechas validation–test y accuracy–macro-F1.

**Decisiones:**
- No se atribuye significancia estadística con solo tres semillas; se reporta variación
  descriptiva.
- Accuracy main16 y full23 no se interpreta como comparación directa porque los espacios
  de etiquetas son distintos.
- La brecha de full23 se investigará mediante métricas por clase y matriz de confusión,
  sin modificar modelos a partir de test.

**Pendiente / carry-over:**
- Analizar métricas por clase y matrices de confusión finales.

---

## 2026-08-05 16:27 -0500 — Fase 5: sincronización y cierre

**Hecho:**
- Sincronizados 10 runs y 441 MB de artefactos MLflow; SQLite pasó `quick_check` y se
  verificaron 14 URI portables.
- Copiados localmente los artefactos finales de test para main16 y full23, incluidas
  matrices de confusión y métricas por clase.
- Marcada la Fase 5 como completada y preparado el tablero de la Fase 6.

**Decisiones:**
- El análisis de matrices se difiere a la Fase 6 para separar ejecución experimental de
  interpretación de resultados.
- Los artefactos binarios permanecen fuera de Git; sus métricas y procedencia sí quedan
  consolidadas en archivos versionados.

**Pendiente / carry-over:**
- Analizar resultados y matrices, documentar limitaciones y preparar el release.

---

## 2026-08-05 16:23 -0500 — Fase 5: evaluación final sobre test

**Hecho:**
- Evaluado una sola vez el modelo main16 baseline semilla 42 mediante `20769`; obtuvo
  macro-F1 test 0.852100 y accuracy 0.919160.
- Evaluado una sola vez el modelo full23 baseline semilla 2026 mediante `20770`; obtuvo
  macro-F1 test 0.612138 y accuracy 0.900501.
- Verificados para ambos perfiles `metrics.json`, métricas por clase y matriz de
  confusión; consolidada la selección y resultados en `final-evaluation.yaml`.

**Decisiones:**
- Los checkpoints se eligieron exclusivamente por macro-F1 de validation antes de
  consultar test; no se harán nuevos ajustes basados en estas métricas test.
- Los directorios de salida son distintos por perfil para impedir sobrescrituras.

**Pendiente / carry-over:**
- Sincronizar MLflow y los artefactos finales, analizar resultados y matrices de
  confusión en la Fase 6.

---

## 2026-08-05 16:04 -0500 — Fase 5: cierre experimental de full23

**Hecho:**
- Confirmado `20767` como `COMPLETED` con exit code `0:0` y duración 11:50.
- Consolidado el tercer run full23, con macro-F1 de validation 0.632172.
- Verificadas las tres semillas full23: macro-F1 medio 0.629718 y desviación estándar
  0.002836; accuracy media 0.898623 y balanced accuracy media 0.632804.

**Decisiones:**
- El run full23 candidato a evaluación final es la semilla 2026, run MLflow
  `29029e09b7034dac8013b07c0897c6b4`, por el mejor macro-F1 de validation.
- Test permanece sin consultar hasta ejecutar una única evaluación de los modelos
  finales seleccionados mediante validation.

**Pendiente / carry-over:**
- Confirmar y ejecutar una vez sobre test el mejor baseline main16 (semilla 42) y el
  mejor baseline full23 (semilla 2026).
- Sincronizar la SQLite y artefactos MLflow después de las evaluaciones finales.

---

## 2026-08-05 15:16 -0500 — Fase 5: avance de full23 baseline

**Hecho:**
- Confirmados `20765` y `20766` como `COMPLETED` con exit code `0:0`.
- Consolidados ambos runs con macro-F1 0.630368 para semilla 42 y 0.626613 para
  semilla 123.
- Confirmada la transición automática de `20767` a ejecución después de finalizar
  completamente el epílogo de `20766`.

**Decisiones:**
- No se sincroniza la SQLite local mientras `20767` permanece activo.
- La menor macro-F1 respecto de `main16` se analizará después de completar las tres
  semillas; full23 incluye siete clases de baja frecuencia.

**Pendiente / carry-over:**
- Esperar `20767`, consolidarlo y cerrar el resumen full23.

---

## 2026-08-05 14:46 -0500 — Fase 5: inicio de full23 baseline

**Hecho:**
- Creada y validada `configs/full23-baseline.yaml` con pérdida `cross_entropy`.
- Verificados manifiesto full23 de 10662 muestras, hash `baed4894…`, SQLite `ok` y
  ausencia de jobs previos.
- Enviados `20765`, `20766` y `20767` para semillas 42, 123 y 2026.
- Confirmado el arranque de `20765`: MLflow HTTP 200, primer checkpoint del run
  `832f77a45bd94319ad0c0f29555e059b` y muestra GPU de 7048 MiB.

**Decisiones:**
- Los tres runs usan baseline, estrategia elegida mediante el promedio de tres semillas
  de `main16`.
- `scontrol` confirmó `afterok:20765` y `afterok:20766`; la razón QOS mostrada
  inicialmente por `squeue` no reemplazó las dependencias.
- CEDIA permanece en `0067f2d` hasta cerrar la cadena para ejecutar un commit idéntico.

**Pendiente / carry-over:**
- Supervisar la cadena y consolidar métricas y consumo de los tres runs full23.

---

## 2026-08-05 14:11 -0500 — Fase 5: cierre experimental de main16

**Hecho:**
- Confirmados `20759`–`20763` como `COMPLETED` con exit code `0:0`.
- Consolidadas las cinco fichas restantes; `experiments/summary.csv` contiene los seis
  runs de `main16` con métricas, procedencia y consumo computacional.
- Corregido el recolector para aceptar `TotalCPU` de Slurm con segundos fraccionarios.

**Decisiones:**
- Baseline es la estrategia ganadora por macro-F1 medio de validation: 0.856086 con
  desviación estándar 0.002987, frente a weighted 0.849512 con desviación 0.010611.
- El mejor run individual weighted (semilla 2026, 0.861258) no reemplaza el criterio
  predefinido por estrategia y tres semillas; baseline también mostró menor variación.

**Pendiente / carry-over:**
- Ejecutar `full23` baseline con semillas 42, 123 y 2026.
- Evaluar una sola vez sobre test los modelos finales después de cerrar `full23`.

---

## 2026-08-05 12:26 -0500 — Fase 5: cadena main16 restante

**Hecho:**
- Verificado el preflight remoto: commit `bcafbdc`, árbol limpio, cero jobs activos,
  configuraciones y manifest disponibles.
- Enviados cinco jobs secuenciales: `20759`, `20760`, `20761`, `20762` y `20763`.
- Confirmado el arranque de `20759`: MLflow HTTP 200, proceso GPU con 5370 MiB y
  primer checkpoint del run `d3745b59a0ad42fe8e23878e54af60ec`.

**Decisiones:**
- Cada sucesor usa `afterok`; un fallo detiene la cadena antes de escribir de nuevo en
  SQLite.
- CEDIA permanece en `bcafbdc` durante toda la cadena para mantener idéntico el commit
  ejecutado; las actualizaciones documentales se desplegarán al terminar.

**Pendiente / carry-over:**
- Supervisar cada transición, revisar logs y recolectar las cinco fichas experimentales.

---

## 2026-08-05 12:12 -0500 — Fase 5: publicación del registro experimental

**Hecho:**
- Publicados en GitHub los commits del registro reproducible de experimentos.
- Actualizado mediante fast-forward el clon de CEDIA hasta `6a22652`, con árbol limpio.

**Decisiones:**
- El recolector queda disponible en CEDIA antes de iniciar los cinco runs restantes,
  para registrar cada resultado con el mismo esquema.

**Pendiente / carry-over:**
- Ejecutar secuencialmente baseline semillas 123 y 2026, seguido de weighted semillas
  42, 123 y 2026 para completar `main16`.

---

## 2026-08-05 12:04 -0500 — Fase 5: registro reproducible de experimentos

**Hecho:**
- Confirmado el job `20755` como `COMPLETED` con exit code `0:0` y duración 16:40.
- Registrado el run MLflow `cb29daac69dd4c9aa8a31ca621d08613`, cuyo macro-F1 de
  validation fue 0.858395.
- Creado un YAML versionado por run y un CSV consolidado con procedencia, asignación,
  consumo observado y métricas.
- Implementado y probado un recolector que consulta `sacct`, el log de Slurm y
  `validation/metrics.json` mediante SSH.

**Decisiones:**
- MLflow continúa como fuente de métricas y artefactos; los registros bajo
  `experiments/` son el índice auditable y versionado.
- Los 7378 MiB de GPU se documentan como muestra puntual, no como consumo máximo.
- CPU promedio se deriva de `TotalCPU / elapsed`; RAM máxima se toma del step de
  entrenamiento y se mantiene separada del proceso batch que hospeda MLflow.

**Pendiente / carry-over:**
- Publicar el recolector y usarlo al finalizar los otros cinco runs de `main16`.
- Automatizar una medición máxima de GPU si CEDIA no expone ese TRES en Slurm.

---

## 2026-08-05 11:24 -0500 — Fase 5: reintento observable de main16

**Hecho:**
- Publicado y desplegado en CEDIA el commit `87ac069`.
- Enviado el baseline `main16` con semilla 42 como job `20755`.
- Confirmado que MLflow respondió HTTP 200 en el intento 8 y que el entrenamiento inició.

**Decisiones:**
- No se encadenan aún los otros cinco runs; primero se confirma la estabilidad del
  entrenamiento reintentado.

**Pendiente / carry-over:**
- Esperar la terminación del job `20755` y revisar su macro-F1 de validation.
- Si termina correctamente, enviar secuencialmente los otros cinco runs de `main16`.

---

## 2026-08-05 11:19 -0500 — Fase 5: diagnóstico del health check de MLflow

**Hecho:**
- Diagnosticado el job `20748`: Gunicorn inició, pero el health check local agotó
  sus 30 intentos antes de comenzar el entrenamiento.
- Modificado el health check para omitir proxies al consultar `127.0.0.1`, conservar
  el error de cada intento y comprobar que el proceso de MLflow siga vivo.
- Añadido el final del log de MLflow al output de Slurm cuando el arranque falla.

**Decisiones:**
- La verificación local no heredará proxies del entorno del cluster.
- Los errores de disponibilidad dejan de silenciarse para que una recurrencia tenga
  una causa observable en el propio log del job.

**Pendiente / carry-over:**
- Publicar el ajuste, actualizar CEDIA y reintentar el primer baseline de `main16`.
- Encadenar los cinco runs restantes solo después de validar el nuevo arranque.

---

## 2026-08-05 02:21 -0500 — Fase 5: cierre de sesión antes de experimentos

**Hecho:**
- Completado el smoke portable `20739` sobre una A100 en 1:31.
- Confirmadas en SQLite las URI `mlflow-artifacts:/` del experimento y del run.
- Sincronizados `mlflow.db` y 16,7 MB de artefactos; la UI local inició correctamente.
- Reforzado `sync-results.sh` con bloqueo, copia atómica, `quick_check` y validación de URI.
- Verificado que no quedaron jobs activos tras interrumpir el envío experimental.

**Decisiones:**
- No se usa ni se necesita `rebase-mlflow.py`.
- Los seis runs `main16` se enviarán mañana de forma secuencial con dependencias `afterok`.
- El smoke portable ejecutó el commit `cba8c7d`; CEDIA quedó actualizado después a `18ac15e`.

**Pendiente / carry-over:**
- Ejecutar baseline y weighted de `main16` con semillas 42, 123 y 2026.
- Elegir la estrategia por macro-F1 de validation antes de lanzar `full23`.

---

## 2026-08-05 01:32 -0500 — Fase 5: validación CEDIA y MLflow portable

**Hecho:**
- Completados bootstrap CPU `20735` y diagnóstico A100 `20736`.
- Verificados torch 2.10.0+cu128, torchvision 0.25.0+cu128, cuDNN 9.1 y CUDA funcional.
- Preparados `main16` y `full23` mediante el job `20737` con hashes reproducibles.
- Reemplazado el FileStore inicial por SQLite y artefactos con URI `mlflow-artifacts:/`.

**Decisiones:**
- Solo se sincronizan `mlflow.db` y `artifacts/`; los `.log` quedan fuera.
- Un servidor MLflow efímero corre dentro de cada job y nunca en `login1`.
- Los experimentos se enviarán secuencialmente para evitar escritores SQLite concurrentes.

**Pendiente / carry-over:**
- Publicar esta corrección, actualizar CEDIA y repetir el smoke test portable.
- Verificar localmente el `mlflow.db` sincronizado antes de los entrenamientos finales.

---

## 2026-08-05 00:44 -0500 — Fase 5: publicación y acceso CEDIA

**Hecho:**
- Creado el repositorio privado `christianbueno1/polysight`.
- Publicadas las ramas `main` y `dev` por SSH.
- Validado el acceso Git de CEDIA y clonado `dev` en `~/projects/polysight`.
- Ajustadas todas las rutas remotas para separar código, datos y artefactos.

**Decisiones:**
- CEDIA usa Git 1.8.3 y una clave OpenSSH dedicada; no requiere GitHub CLI.
- El código vive en `~/projects/polysight`, el ZIP en `~/datasets` y los resultados
  en `~/projects/polysight-storage`.

**Pendiente / carry-over:**
- Publicar este ajuste de rutas y actualizar el clon remoto.
- Ejecutar bootstrap y diagnóstico mediante Slurm.

---

## 2026-08-04 22:44 -0500 — Fase 4: CEDIA, Slurm y sincronización

**Hecho:**
- Creados jobs Slurm para bootstrap, diagnóstico, datos, smoke, training y test.
- Creados scripts locales Git/SSH/rsync que usan exclusivamente el alias `cedia`.
- Implementada la sincronización y reescritura portable de URI de MLflow.
- Documentado el flujo operativo y validada la sintaxis de todos los scripts.

**Decisiones:**
- Los jobs abortan sin `SLURM_JOB_ID` o si el hostname comienza con `login`.
- El recurso inicial es una A100 de 40 GB, 8 CPU y 32 GB en `gpu-dev`.
- El entorno remoto reutiliza `pytorch/2.2` y `cuda/12.4`; no instala otro PyTorch.

**Pendiente / carry-over:**
- La autenticación local de `gh` está vencida; falta crear/publicar el repositorio privado.
- Después de publicar `dev`, clonar en CEDIA y ejecutar diagnóstico, datos y smoke test.

---

## 2026-08-04 22:38 -0500 — Fase 3: pipeline PyTorch

**Hecho:**
- Implementados configuración YAML, Dataset, transforms y DataLoaders.
- Implementado EfficientNet-B0 preentrenado con cabeza para 16 o 23 clases.
- Implementado entrenamiento congelado/fine-tuning con AMP, checkpoints y reanudación.
- Implementadas evaluación, predicción top-3, matrices de confusión y MLflow.
- Creado `uv.lock`; pasan 5 pruebas locales y Ruff sin errores.

**Decisiones:**
- `run_training` rechaza CPU para impedir entrenamiento local accidental.
- Los pesos de clase se calculan solo desde training y se normalizan a media 1.
- Test no se consulta durante training; requiere el comando explícito de evaluación.

**Pendiente / carry-over:**
- Validar torch, torchvision, CUDA, cuDNN y las pruebas omitidas en un nodo GPU de CEDIA.
- Crear jobs Slurm y sincronización Git/rsync/MLflow.

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
