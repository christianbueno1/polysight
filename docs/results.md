# Resultados experimentales

## Alcance y protocolo

Los resultados de `validation` resumen tres semillas (42, 123 y 2026) y se expresan
como media ± desviación estándar muestral. Los resultados oficiales de `test`
pertenecen a una única evaluación del checkpoint elegido previamente por macro-F1 de
validation. Una inferencia posterior con los mismos inputs regeneró exclusivamente los
artefactos de matriz faltantes y reprodujo exactamente las métricas oficiales.

Test no se utilizó para elegir estrategia, semilla ni hiperparámetros. Sus resultados
no deben emplearse para realizar nuevos ajustes en esta ronda experimental.

Fuentes versionadas:

- `experiments/summary.csv`: runs de entrenamiento y validation.
- `experiments/final-evaluation.yaml`: selección y evaluación final sobre test.
- `experiments/runs/*.yaml`: procedencia y consumo de cada job.

## Validation: comparación de estrategias y perfiles

| Perfil | Estrategia | Accuracy | Balanced accuracy | Macro-F1 | Top-3 accuracy | Weighted-F1 |
|---|---|---:|---:|---:|---:|---:|
| main16 | baseline | 0.913643 ± 0.002046 | 0.859631 ± 0.003856 | **0.856086 ± 0.002987** | 0.992362 ± 0.001103 | 0.912909 ± 0.001415 |
| main16 | weighted | 0.904519 ± 0.004456 | **0.867232 ± 0.010778** | 0.849512 ± 0.010611 | 0.992998 ± 0.001273 | 0.905985 ± 0.004073 |
| full23 | baseline | 0.898623 ± 0.001656 | 0.632804 ± 0.005018 | 0.629718 ± 0.002836 | 0.979349 ± 0.001084 | 0.894709 ± 0.002560 |

Baseline fue elegido para full23 porque el criterio previo era macro-F1 medio de las
tres semillas. En main16 superó a weighted por 0.006574 y presentó menor variación
(0.002987 frente a 0.010611). Weighted mejoró balanced accuracy en 0.007601, pero esa
mejora no se tradujo en mayor macro-F1 ni estabilidad.

El resultado individual weighted de la semilla 2026 (macro-F1 0.861258) fue el mayor
run de main16, pero no reemplaza la comparación agregada definida antes de consultar
test.

## Test: modelos finales

| Perfil | Modelo seleccionado | Accuracy | Balanced accuracy | Macro-F1 | Top-3 accuracy | Weighted-F1 |
|---|---|---:|---:|---:|---:|---:|
| main16 | baseline, semilla 42 | 0.919160 | 0.842413 | **0.852100** | 0.996817 | 0.917500 |
| full23 | baseline, semilla 2026 | 0.900501 | 0.615032 | **0.612138** | 0.984355 | 0.894388 |

La diferencia entre macro-F1 de validation del checkpoint seleccionado y test fue
-0.006295 para main16 y -0.020035 para full23. No se reentrenó ni volvió a seleccionar
ningún modelo después de observar estas diferencias.

## Interpretación agregada

- Main16 mantiene cercanía entre accuracy, balanced accuracy y macro-F1. La diferencia
  test entre accuracy y macro-F1 es 0.067060.
- Full23 presenta accuracy test de 0.900501, pero macro-F1 de 0.612138 y balanced
  accuracy de 0.615032. La diferencia accuracy–macro-F1 asciende a 0.288363.
- Esta divergencia indica que la accuracy global está dominada por clases frecuentes y
  no resume adecuadamente el desempeño de las siete clases escasas incorporadas en
  full23.
- Top-3 permanece alto en ambos perfiles. Esto indica que la etiqueta correcta suele
  recibir probabilidad alta, aunque no siempre ocupa la primera posición.
- Las métricas agregadas no identifican qué pares de clases producen los errores. Esa
  conclusión requiere el análisis separado de métricas por clase y matrices de
  confusión.

Con solo tres semillas se puede describir variación observada, pero no afirmar
significancia estadística ni construir una estimación robusta de incertidumbre. Tampoco
deben compararse las accuracies de main16 y full23 como si fueran exactamente la misma
tarea: sus espacios de etiquetas contienen 16 y 23 clases, respectivamente.

## Métricas por clase y matrices de confusión

Las matrices oficiales representan conteos absolutos: filas son clases reales y
columnas son predicciones. Los artefactos derivados añaden la tabla exacta de conteos y
una visualización normalizada por fila. Esta última permite comparar clases con soportes
distintos porque cada fila suma 100%.

### Main16

Las clases con menor F1 en test fueron:

| Clase | Soporte | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| ulcerative-colitis-grade-1 | 30 | 0.650000 | 0.433333 | 0.520000 |
| ulcerative-colitis-grade-3 | 20 | 0.590909 | 0.650000 | 0.619048 |
| esophagitis-a | 60 | 0.655738 | 0.666667 | 0.661157 |
| impacted-stool | 20 | 0.857143 | 0.600000 | 0.705882 |
| ulcerative-colitis-grade-2 | 66 | 0.704225 | 0.757576 | 0.729927 |
| esophagitis-b-d | 39 | 0.931034 | 0.692308 | 0.794118 |

La diagonal equivale a 13/30 aciertos para colitis grado 1, 13/20 para grado 3,
40/60 para esophagitis-a, 12/20 para impacted-stool, 50/66 para colitis grado 2 y
27/39 para esophagitis-b-d.

Visualmente, las confusiones más marcadas aparecen dentro del continuo de grados de
colitis, entre esophagitis-a y z-line/esophagitis-b-d, y entre las dos clases de pólipos
teñidos. La tabla derivada permite auditar los conteos fuera de la diagonal sin inferirlos
desde el color del heatmap.

Las clases más sólidas fueron retroflex-stomach (F1 1.000000), bbps-0-1 (0.989691),
pylorus (0.983498), cecum (0.977049) y bbps-2-3 (0.968661).

### Full23

Seis de las siete clases escasas añadidas a full23 obtuvieron precision, recall y F1
iguales a cero:

| Clase | Soporte test | F1 |
|---|---:|---:|
| barretts | 6 | 0.000000 |
| barretts-short-segment | 8 | 0.000000 |
| hemorrhoids | 1 | 0.000000 |
| ileum | 1 | 0.000000 |
| ulcerative-colitis-grade-1-2 | 2 | 0.000000 |
| ulcerative-colitis-grade-2-3 | 4 | 0.000000 |

La séptima, ulcerative-colitis-grade-0-1, alcanzó F1 0.600000 con soporte 5. Entre las
clases compartidas con main16, colitis grado 1 volvió a ser la más débil (F1 0.415094,
recall 0.366667). El heatmap muestra que las confusiones se concentran en los grados
adyacentes de colitis y en la región esofágica, mientras las clases frecuentes conservan
una diagonal dominante.

Estos resultados explican la coexistencia de accuracy 0.900501 y macro-F1 0.612138:
las clases frecuentes tienen buen desempeño, pero cada clase sin aciertos pesa lo mismo
en macro-F1. No es evidencia de que el modelo full23 resuelva adecuadamente las 23
clases.

### Regeneración de artefactos

Los jobs `22953` y `22954` ejecutaron inferencia con los checkpoints y manifests
congelados, sin entrenamiento ni selección posterior. `metrics.json` y
`per-class-metrics.csv` resultaron idénticos byte por byte a los oficiales. Las salidas
se guardaron en `final-evaluation-derived/`, sin sobrescribir la evaluación original, y
su procedencia y hashes están registrados en `experiments/final-evaluation.yaml`.

## Rendimiento y consumo computacional

Los nueve entrenamientos se ejecutaron sobre una A100 SXM4 de 40 GB, con 8 CPU y 32 GiB
de RAM solicitados por job.

| Perfil/estrategia | Runs | Épocas promedio | Tiempo promedio | Tiempo total | CPU promedio | MaxRSS promedio | MaxRSS máximo |
|---|---:|---:|---:|---:|---:|---:|---:|
| main16 baseline | 3 | 31.0 | 14:58 | 44:53 | 5.843 | 4235.9 MiB | 4249.9 MiB |
| main16 weighted | 3 | 24.7 | 11:52 | 35:37 | 5.907 | 4237.4 MiB | 4283.1 MiB |
| full23 baseline | 3 | 27.3 | 13:34 | 40:41 | 5.870 | 4228.4 MiB | 4242.5 MiB |

En conjunto se consumieron 2:01:11 de tiempo de asignación A100 y aproximadamente
11.86 CPU-h efectivas. El promedio ponderado fue 5.87 de las 8 CPU asignadas (~73 %).
La memoria máxima del step de entrenamiento se mantuvo alrededor de 4.13 GiB, muy por
debajo de los 32 GiB reservados.

Weighted terminó antes principalmente porque early stopping produjo 23, 20 y 31 épocas,
frente a 32, 32 y 29 para main16 baseline. Full23 ejecutó 28, 31 y 23 épocas. Estas
cantidades provienen de los steps `val_macro_f1` registrados en MLflow.

Solo existen tres muestras puntuales de memoria GPU: 7378, 5370 y 7048 MiB. No son
máximos y no permiten estimar utilización promedio, potencia ni eficiencia de la A100.
Slurm tampoco publicó TRES de memoria o utilización GPU. Por tanto, no se afirma que la
reserva de 40 GB pueda reducirse basándose únicamente en estas muestras.

Las evaluaciones finales duraron 39 segundos para main16 y 25 segundos para full23. No
se incluyen en las 2:01:11 de entrenamiento.

En estabilidad predictiva, main16 baseline y full23 baseline tuvieron desviaciones de
macro-F1 de 0.002987 y 0.002836. Main16 weighted fue más variable (0.010611), además de
obtener menor macro-F1 medio.

## Conclusiones

1. EfficientNet-B0 con transferencia de aprendizaje ofrece un baseline sólido para
   main16: macro-F1 test 0.852100, accuracy 0.919160 y resultados estables entre tres
   semillas.
2. Ponderar la entropía cruzada no mejoró el criterio principal agregado. Aumentó
   balanced accuracy media, pero redujo macro-F1 medio y mostró mayor variación.
3. Full23 no resuelve adecuadamente las 23 clases. Su accuracy cercana a 0.90 coexiste
   con macro-F1 0.612138 y seis clases sin aciertos en test.
4. La escasez extrema y la proximidad visual/semántica entre categorías son el principal
   límite observado. Agregar clases con 6–53 imágenes totales no basta para obtener un
   clasificador equilibrado mediante el protocolo actual.
5. Main16 puede considerarse un resultado experimental reproducible dentro de este
   dataset y split. No constituye validación clínica ni evidencia suficiente para uso
   diagnóstico.

## Limitaciones y amenazas a la validez

### Validez interna

- HyperKvasir no aporta identificadores suficientes de paciente o procedimiento. El
  split no puede garantizar independencia clínica entre train, validation y test.
- Los duplicados exactos permanecen en un único split, pero los posibles duplicados
  perceptuales detectados mediante dHash solo se reportaron; no fueron adjudicados
  manualmente ni agrupados automáticamente.
- Las semillas controlan Python, NumPy y PyTorch, pero `torch.backends.cudnn.benchmark`
  está habilitado. No se garantiza repetibilidad bit a bit de kernels CUDA.
- Los checkpoints se eligieron correctamente sin mirar test, pero solo se exploraron
  dos pérdidas sobre una arquitectura y un conjunto fijo de hiperparámetros.

### Validez estadística

- Tres semillas permiten describir variación, no demostrar significancia estadística.
- Existe una sola partición 70/15/15. No se realizó validación cruzada ni evaluación en
  múltiples cohortes.
- Varias clases full23 tienen soporte test entre 1 y 8. Sus métricas son extremadamente
  discretas e inestables; un solo acierto cambia sustancialmente recall y F1.
- La evaluación test única evita ajuste posterior, pero no proporciona intervalos de
  confianza ni estima variación entre posibles tests.

### Validez de constructo y medición

- Las etiquetas se tratan como clases nominales independientes, aunque grados de
  colitis y esophagitis tienen relación ordinal y fronteras visuales cercanas.
- Accuracy y weighted-F1 están dominadas por clases frecuentes; no deben presentarse
  aisladamente como evidencia de desempeño multiclase equilibrado.
- No se evaluaron calibración, sensibilidad/especificidad por umbral, incertidumbre,
  rechazo de casos fuera de distribución ni desempeño por dispositivo o centro.
- La tabla de conteos y la versión normalizada proceden de una inferencia posterior con
  inputs congelados; no formaron parte del job oficial original. La coincidencia exacta
  de métricas respalda su uso descriptivo, no nuevos ajustes experimentales.

### Validez externa y clínica

- Todo el análisis usa HyperKvasir; no existe validación externa en otro hospital,
  equipo endoscópico, población o protocolo de captura.
- El preentrenamiento ImageNet introduce conocimiento útil, pero no elimina el cambio
  de dominio entre imágenes naturales y endoscopia.
- Los datos son frames etiquetados. El estudio no evalúa dependencia temporal en video,
  múltiples hallazgos por frame ni integración en un flujo clínico.
- Top-3 alto no equivale a utilidad clínica: un sistema real necesita criterios de
  seguridad, calibración, revisión humana y evaluación prospectiva.

## Alcance de las afirmaciones

Los resultados permiten afirmar que el pipeline reproduce una comparación controlada
de EfficientNet-B0 sobre dos perfiles de HyperKvasir y que main16 es más robusto bajo
este protocolo. No permiten afirmar generalización clínica, superioridad frente a otras
arquitecturas, desempeño por paciente ni capacidad diagnóstica autónoma.
