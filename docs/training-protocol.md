# Semillas, pesos iniciales y número de épocas

Este documento explica las decisiones del protocolo de entrenamiento de PolySight y
aclara qué partes tienen una justificación técnica, cuáles son convenciones
reproducibles y cuáles no fueron optimizadas sistemáticamente.

## ¿Es necesario repetir los experimentos?

No es necesario repetir los entrenamientos para cerrar la Fase 6 ni para validar el
cambio que genera matrices de confusión normalizadas.

Conviene distinguir tres operaciones:

1. **Entrenamiento:** produce los checkpoints y no debe repetirse para el release
   actual.
2. **Evaluación final sobre test:** ya se ejecutó una sola vez por perfil y permanece
   cerrada para evitar ajustes posteriores basados en test.
3. **Pruebas del código:** pueden y deben ejecutarse en un entorno con PyTorch; no
   entrenan modelos ni consultan el dataset experimental.

Las matrices normalizadas se producirán en evaluaciones futuras. Para crearlas
retroactivamente sería necesario volver a ejecutar inferencia sobre test con los
checkpoints congelados. No haría falta reentrenar, pero sí se rompería la política
documentada de una única consulta a test. Los PNG históricos tampoco contienen
información suficiente para reconstruir con exactitud todos los conteos.

## Semillas de entrenamiento

Los experimentos utilizaron las semillas `42`, `123` y `2026`. No existe una
propiedad matemática o de PyTorch que haga que esos valores produzcan mejores modelos.
Son identificadores arbitrarios de tres estados pseudoaleatorios distintos.

Lo importante es que las semillas sean diferentes, queden registradas y se apliquen
consistentemente. Tres repeticiones permiten describir la variación observada, pero no
demostrar significancia estadística ni caracterizar completamente la distribución de
resultados.

El repositorio no documenta una justificación científica especial para los números
elegidos. `42` es una convención habitual, mientras `123` y `2026` aportan dos estados
distintos fácilmente identificables. Su valor numérico no aumenta por sí mismo el
rendimiento.

### Qué controla la semilla

Antes de construir los dataloaders y el modelo, `seed_everything` configura:

```python
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
```

Esto influye en:

- la inicialización de la nueva cabeza clasificadora;
- el orden de las muestras de entrenamiento;
- los recortes, rotaciones y transformaciones aleatorias;
- dropout;
- operaciones estocásticas de PyTorch y CUDA.

El código mantiene `torch.backends.cudnn.benchmark = True`. Por ello, una misma semilla
no garantiza repetibilidad bit a bit de todos los kernels CUDA. El protocolo es
reproducible metodológicamente, pero no completamente determinista a nivel binario.

### La semilla de entrenamiento no cambia el split

Todos los runs de un perfil consumen el mismo `manifest.csv`. Cambiar `--seed` modifica
la aleatoriedad del entrenamiento, pero no reasigna imágenes entre train, validation y
test.

La preparación inicial del manifest tiene su propia semilla. Esa operación es separada
y se ejecutó antes de los entrenamientos. Mantener fijo el manifest permite comparar
semillas sobre exactamente la misma partición de datos.

## Pesos iniciales del modelo

La inicialización es una combinación de pesos preentrenados y pesos aleatorios.

### Backbone preentrenado

Las configuraciones principales declaran:

```yaml
model:
  architecture: efficientnet_b0
  pretrained: true
  weights_path: ${POLYSIGHT_WEIGHTS_PATH}
  dropout: 0.2
```

En CEDIA, `POLYSIGHT_WEIGHTS_PATH` apunta a:

```text
efficientnet_b0_rwightman-7f5810bc.pth
```

Las capas convolucionales de EfficientNet-B0 comienzan con pesos preentrenados en
ImageNet. Si no se proporciona el archivo local y `pretrained` sigue activo, el código
solicita `EfficientNet_B0_Weights.DEFAULT` a torchvision.

El backbone, por tanto, no empieza desde valores aleatorios. Esta reutilización de
representaciones aprendidas previamente es transferencia de aprendizaje.

### Cabeza clasificadora aleatoria

La cabeza de ImageNet para 1.000 clases se descarta y se reemplaza por:

```python
nn.Sequential(
    nn.Dropout(p=0.2),
    nn.Linear(in_features, num_classes),
)
```

La nueva capa lineal sí comienza con pesos y bias inicializados aleatoriamente por
PyTorch. `nn.Linear` aplica su inicialización predeterminada al construirse, y el estado
pseudoaleatorio depende de la semilla configurada antes de crear el modelo.

En resumen:

```text
Backbone de EfficientNet-B0 -> pesos preentrenados en ImageNet
Cabeza clasificadora       -> pesos aleatorios nuevos
```

Durante evaluación se carga el `model_state` completo desde `best.pt`. La inicialización
temporal del objeto no afecta las predicciones porque es reemplazada por los pesos del
checkpoint.

## Número de épocas

Las configuraciones completas usan los mismos valores:

```yaml
training:
  head_epochs: 3
  finetune_epochs: 30
  head_learning_rate: 0.001
  backbone_learning_rate: 0.0001
  weight_decay: 0.0001
  patience: 7
```

El presupuesto máximo es de 33 épocas, pero early stopping puede terminar antes.

### Etapa 1: cabeza clasificadora

Durante las primeras tres épocas:

- el backbone permanece congelado;
- solamente se entrena la nueva cabeza;
- se usa AdamW con learning rate `0.001` y weight decay `0.0001`;
- `CosineAnnealingLR` usa `T_max=3`.

Esta etapa adapta primero la cabeza aleatoria al nuevo problema sin modificar
inmediatamente las representaciones preentrenadas.

### Etapa 2: fine-tuning

Durante un máximo de 30 épocas:

- se libera el backbone;
- el backbone usa learning rate `0.0001`;
- la cabeza conserva learning rate `0.001`;
- se mantiene weight decay `0.0001`;
- `CosineAnnealingLR` usa `T_max=30`;
- se usa mixed precision en CUDA;
- early stopping emplea paciencia de siete épocas.

El learning rate del backbone es diez veces menor porque sus pesos ya contienen
representaciones aprendidas en ImageNet.

### Early stopping y selección del checkpoint

Al finalizar cada época se calcula macro-F1 sobre validation. Cuando la métrica
mejora, se reinicia el contador de paciencia y se actualiza `best.pt`. Durante
fine-tuning, siete épocas consecutivas sin mejora detienen el entrenamiento.

El modelo final no es necesariamente el de la última época, sino el checkpoint con
mejor macro-F1 de validation.

## Épocas realmente ejecutadas

| Experimento | Semillas | Épocas ejecutadas |
|---|---|---|
| `main16 baseline` | 42, 123, 2026 | 32, 32, 29 |
| `main16 weighted` | 42, 123, 2026 | 23, 20, 31 |
| `full23 baseline` | 42, 123, 2026 | 28, 31, 23 |

Las diferencias se deben al early stopping. Estas cantidades provienen de los steps de
`val_macro_f1` registrados en MLflow.

## Alcance de la justificación

Los valores `head_epochs=3`, `finetune_epochs=30` y `patience=7` son decisiones
heurísticas razonables para transferencia de aprendizaje, pero el proyecto no registra
una búsqueda sistemática que demuestre que sean óptimos.

No se compararon formalmente alternativas como:

```text
head_epochs:     1, 3, 5
finetune_epochs: 20, 30, 50
patience:        5, 7, 10
```

Por tanto, puede afirmarse que el protocolo se aplicó consistentemente a todos los
runs, pero no que `3 + 30` sea la duración óptima. Una investigación futura podría
comparar más semillas e hiperparámetros usando exclusivamente train y validation,
manteniendo test cerrado.

## Referencias en el repositorio

- Construcción del modelo: `src/polysight/model.py`.
- Semillas, etapas, optimizadores y early stopping: `src/polysight/train.py`.
- Valores del protocolo: `configs/main16-baseline.yaml`,
  `configs/main16-weighted.yaml` y `configs/full23-baseline.yaml`.
- Resultados y épocas ejecutadas: `docs/results.md`.
- Selección final: `experiments/final-evaluation.yaml`.
