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
