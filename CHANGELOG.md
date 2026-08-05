# CHANGELOG

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
