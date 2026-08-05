# Resultados experimentales

## Alcance y protocolo

Los resultados de `validation` resumen tres semillas (42, 123 y 2026) y se expresan
como media ± desviación estándar muestral. Los resultados de `test` pertenecen a una
única evaluación del checkpoint elegido previamente por macro-F1 de validation.

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

Las matrices finales representan conteos absolutos: filas son clases reales y columnas
son predicciones. No están normalizadas. Por ello las celdas de clases con soporte 1–8
son casi invisibles frente a clases con soporte cercano a 170; recall y F1 por clase son
la fuente cuantitativa adecuada para interpretarlas.

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
teñidos. Esta lectura es cualitativa porque el pipeline guardó el heatmap, pero no una
tabla con los conteos fuera de la diagonal.

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

### Limitación del artefacto

Para futuras rondas, `save_evaluation_artifacts` debería guardar además la matriz cruda
como CSV y una segunda visualización normalizada por fila. No se repite la evaluación
test actual para reconstruirlas: las conclusiones presentes usan exclusivamente los
artefactos producidos en la evaluación única ya cerrada.
