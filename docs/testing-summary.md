# Resumen de la evaluación final sobre test

Este documento explica los resultados de la evaluación final de los modelos
`main16` y `full23`. Los checkpoints se seleccionaron usando exclusivamente el
macro-F1 de validation y se evaluaron una sola vez sobre test, para evitar usar
test como fuente de ajustes del modelo.

La procedencia completa de los modelos, jobs y artefactos está registrada en
[`experiments/final-evaluation.yaml`](../experiments/final-evaluation.yaml).

## Resultados agregados

| Perfil | Accuracy | Balanced accuracy | Macro-F1 | Weighted-F1 | Top-3 accuracy |
|---|---:|---:|---:|---:|---:|
| `main16` baseline, semilla 42 | 91.92% | 84.24% | 85.21% | 91.75% | 99.68% |
| `full23` baseline, semilla 2026 | 90.05% | 61.50% | 61.21% | 89.44% | 98.44% |

### Interpretación de las métricas

- **Accuracy:** proporción total de imágenes clasificadas correctamente.
- **Balanced accuracy:** promedio del recall de todas las clases; reduce el efecto
  de que las clases frecuentes dominen el resultado.
- **Macro-F1:** promedio del F1 asignando el mismo peso a cada clase. Es una métrica
  importante cuando existe desbalance de clases.
- **Weighted-F1:** promedio del F1 ponderado por el número de ejemplos de cada
  clase; las clases frecuentes tienen mayor influencia.
- **Top-3 accuracy:** proporción de casos en los que la clase correcta aparece entre
  las tres predicciones con mayor probabilidad.

## Interpretación de `main16`

El modelo `main16-baseline-seed42` alcanzó 91.92% de accuracy y 85.21% de
macro-F1. La diferencia moderada entre ambas métricas indica que el rendimiento
no es idéntico en todas las clases, aunque se mantiene razonablemente equilibrado.

Su macro-F1 de validation fue 85.84%, muy cercano al 85.21% obtenido en test.
Esta cercanía indica que el rendimiento observado en validation se trasladó bien
al conjunto de test bajo este split.

### Lectura de la matriz de confusión

En la matriz de confusión:

- Cada fila representa la clase real.
- Cada columna representa la clase predicha.
- Las celdas de la diagonal son aciertos.
- Las celdas fuera de la diagonal son errores de clasificación.
- Un azul más oscuro representa un número absoluto mayor de imágenes.

La diagonal claramente marcada confirma que la mayoría de las imágenes fueron
clasificadas correctamente.

![Matriz de confusión de main16](../artifacts/cedia/final-evaluation/main16-baseline-seed42/confusion-matrix.png)

### Clases con mejor desempeño

| Clase | Aciertos / total | Recall | F1 |
|---|---:|---:|---:|
| `retroflex-stomach` | 115/115 | 100.00% | 100.00% |
| `retroflex-rectum` | 59/59 | 100.00% | 96.72% |
| `pylorus` | 149/150 | 99.33% | 98.35% |
| `bbps-0-1` | 96/97 | 98.97% | 98.97% |
| `bbps-2-3` | 170/172 | 98.84% | 96.87% |
| `cecum` | 149/151 | 98.68% | 97.70% |

`retroflex-stomach` obtuvo precision, recall y F1 perfectos. En
`retroflex-rectum`, el recall perfecto significa que se encontraron todos los casos
reales, mientras que su precision inferior a 100% indica que algunas imágenes de
otras clases fueron predichas incorrectamente como `retroflex-rectum`.

### Confusiones relevantes

#### Pólipos teñidos

Existe confusión en ambas direcciones entre `dyed-lifted-polyps` y
`dyed-resection-margins`. A pesar de ello, ambas clases mantienen resultados altos:

| Clase | Recall | F1 |
|---|---:|---:|
| `dyed-lifted-polyps` | 95.33% | 94.08% |
| `dyed-resection-margins` | 92.57% | 93.84% |

#### Esofagitis y `z-line`

La matriz muestra confusiones entre `esophagitis-a`, `esophagitis-b-d` y
`z-line`, especialmente entre `esophagitis-a` y `z-line`.

| Clase | Aciertos / total | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| `esophagitis-a` | 40/60 | 65.57% | 66.67% | 66.12% |
| `esophagitis-b-d` | 27/39 | 93.10% | 69.23% | 79.41% |
| `z-line` | 126/140 | 86.30% | 90.00% | 88.11% |

La alta precision y el menor recall de `esophagitis-b-d` significan que sus
predicciones suelen ser correctas, pero el modelo deja escapar varios casos reales
y los asigna a otras clases.

#### Grados de colitis ulcerativa

Las tres clases de colitis forman el grupo más difícil. El modelo confunde grados
vecinos y `ulcerative-colitis-grade-1` presenta el rendimiento más bajo de
`main16`.

| Clase | Aciertos / total | Recall | F1 |
|---|---:|---:|---:|
| `ulcerative-colitis-grade-1` | 13/30 | 43.33% | 52.00% |
| `ulcerative-colitis-grade-2` | 50/66 | 75.76% | 72.99% |
| `ulcerative-colitis-grade-3` | 13/20 | 65.00% | 61.90% |

El patrón muestra dificultad para separar los grados, pero estos resultados por sí
solos no permiten determinar la causa. Podrían intervenir semejanza visual, pocos
ejemplos, variabilidad de las imágenes o ambigüedad en las etiquetas.

#### `impacted-stool`

El modelo acertó 12 de 20 imágenes de `impacted-stool`, con recall de 60% y F1 de
70.59%. El bajo soporte hace que su diagonal se vea clara en comparación con clases
de aproximadamente 150 ejemplos, pero ocho errores de veinte siguen siendo una
proporción relevante.

### Limitación de la visualización

La matriz muestra conteos absolutos y utiliza una sola escala de color. Por ello, la
intensidad de una celda combina dos factores: el número de ejemplos de la clase y su
proporción de aciertos. No es suficiente comparar solamente la oscuridad de las
celdas entre filas con soportes diferentes.

El pipeline producirá en evaluaciones futuras una matriz adicional normalizada por
fila, donde cada celda se interpreta como porcentaje. No se genera retroactivamente
para este test cerrado porque no se conservaron sus conteos completos. Para los
valores actuales, la fuente cuantitativa es
[`per-class-metrics.csv`](../artifacts/cedia/final-evaluation/main16-baseline-seed42/per-class-metrics.csv).

## Interpretación de `full23`

El modelo `full23-baseline-seed2026` obtuvo 90.05% de accuracy, pero solamente
61.21% de macro-F1. La diferencia revela un fuerte efecto del desbalance: el buen
rendimiento de las clases frecuentes domina la accuracy y el weighted-F1, mientras
que varias clases escasas tienen un rendimiento bajo.

Seis clases escasas obtuvieron F1 igual a cero. En consecuencia, `full23` todavía
no proporciona una clasificación equilibrada de sus 23 clases, aunque su accuracy
global sea alta.

## Conclusión

`main16` es el baseline más estable y equilibrado del experimento. `full23` conserva
un buen rendimiento global en las clases dominantes, pero presenta dificultades
importantes en las clases minoritarias. Las accuracies de ambos perfiles no deben
compararse como si resolvieran exactamente el mismo problema, porque sus espacios de
etiquetas contienen 16 y 23 clases, respectivamente.

Estos resultados describen el comportamiento experimental en HyperKvasir y en el
split utilizado. No constituyen evidencia de validación clínica ni garantizan la
generalización a otros datasets o entornos.
