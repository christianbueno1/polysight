## revisar job
```bash
squeue -j 20735 -o "%i|%T|%M|%R"; sacct -j 20735 --format=JobID,State,Elapsed,ExitCode -n -P 2>/dev/null || true; tail -n 35 slurm-polysight-bootstrap-20735.out 2>/dev/null || true

|# run jobs
sbatch slurm/bootstrap.sbatch
sbatch slurm/diagnose.sbatch
sbatch slurm/prepare-data.sbatch
sbatch slurm/smoke.sbatch

# Bootstrap:
# Bootstrap: prepara el entorno de ejecución en el cluster — carga los módulos de PyTorch/CUDA, 
# valida que la versión de Python sea la 3.11 esperada, crea el venv (.venv-cluster) heredando 
# esos paquetes del sistema, e instala el proyecto ahí dentro. Es el paso base del que dependen
# todos los demás jobs.

# Diagnose:
# diagnose confirma que el entorno GPU del cluster funciona de punta a punta antes de gastar tiempo/cómputo real: 
# verifica que la GPU A100 asignada es visible y utilizable por PyTorch (CUDA, cuDNN, conteo de devices), 
# y corre un test rápido del código de modelo/métricas para asegurar que la lógica central del 
# pipeline (arquitectura, pesos de clase, cálculo de macro-F1) está sana — todo antes de tocar 
# datos reales o lanzar los seis entrenamientos.

# Prepare data:
# prepare-data toma el ZIP crudo de HyperKvasir, lo descomprime y organiza en el almacenamiento 
# del cluster, y genera los manifiestos de train/val/test (splits estratificados) tanto para el 
# perfil main16 como para full23 — dejando el dataset listo para que smoke y train puedan 
# consumirlo directamente.

# Smoke:
# smoke corre un entrenamiento mínimo y rápido (smoke-main16.yaml, una sola semilla) contra los 
# datos ya preparados, con el servidor MLflow levantado, para confirmar que todo el pipeline de 
# entrenamiento —desde la carga de datos hasta el logging de métricas— funciona correctamente 
# antes de lanzar los seis entrenamientos completos y costosos.

# Train:
# train es el job genérico y reutilizable que ejecuta un entrenamiento completo de 
# EfficientNet-B0 (cabeza + fine-tuning) para un config y semilla dados, recibidos por variables 
# de entorno (CONFIG_PATH, RUN_SEED); es el mismo script el que corre las 
# 6 combinaciones (baseline/weighted × 3 semillas) encadenadas con afterok, y su única diferencia 
# real entre baseline y weighted es el tipo de loss usada.

# Evaluate:
# evaluate es el paso final: toma un config y un checkpoint 
# específicos (el modelo ganador, ya elegido por macro-F1 en validation), y corre una única evaluación 
# sobre el split de test —nunca visto durante entrenamiento ni selección de modelo—, guardando los 
# resultados en un directorio dedicado, sin tocar MLflow ni permitir ajustes posteriores basados 
# en ese resultado.
```

## Sincronizar desde CEDIA a local
```bash
scripts/cluster/sync-results.sh
```

##  Comprueba actividad con:
```bash
cd ~/projects/polysight
tail -n 50 slurm-polysight-train-20755.out

sstat -j 20755.batch,20755.0 \
--format=JobID,AveCPU,AveRSS,MaxRSS,Elapsed

# Para observar la GPU dentro de la asignación:
srun --jobid=20755 --overlap -N1 -n1 \
nvidia-smi --query-compute-apps=pid,used_memory \
--format=csv

# Importante: el código actual no imprime progreso por época. Después de iniciar, el archivo Slurm puede permanecer silencioso durante todo el entrenamiento y solo imprime
# el checkpoint final al terminar. Por tanto, un tail sin líneas nuevas no implica que esté bloqueado.

# También puedes revisar si ya creó checkpoints:
find ~/projects/polysight-storage/runs/main16-baseline \
-type f \( -name 'last.pt' -o -name 'best.pt' \) \
-printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null

###
# Tu versión de Slurm no admite Elapsed en sstat. Usa:
sstat -j 20755.batch,20755.0 \
--format=JobID,AveCPU,AveRSS,MaxRSS

# Y para el tiempo:
squeue -j 20755 -o "%.18i %.2t %.10M %.10l %R"

# Puedes vigilar los checkpoints cada cierto tiempo con:
watch -n 60 "find ~/projects/polysight-storage/runs/main16-baseline \
-type f \( -name last.pt -o -name best.pt \) \
-printf '%TY-%Tm-%Td %TH:%TM:%TS %f\n'"

# No hace falta cancelar ni intervenir. Esperemos a que termine 20755; después revisamos su macro-F1 y, si finaliza correctamente, enviamos los otros cinco runs secuenciales.

###
squeue -j 20759,20760,20761,20762,20763 \
-o "%.18i %.2t %.10M %.30R"

tail -n 50 ~/projects/polysight/slurm-polysight-train-20759.out
###
ssh -F /home/chris/.ssh/config cedia 'cd ~/projects/polysight && sacct -j 20759,20760,20761,20762,20763 --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS -n -P && for job in 20759 20760 20761 20762 20763; do echo JOB=${job}; tail -n 8 slurm-polysight-train-${job}.out; done'
# dividir en multiples líneas para que no se rompa el scroll de la terminal:
# Opción 1: Barras invertidas (\) y comillas dobles (La más recomendada)
ssh -F /home/chris/.ssh/config cedia "
  cd ~/projects/polysight && \
  sacct -j 20759,20760,20761,20762,20763 \
    --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS -n -P && \
  for job in 20759 20760 20761 20762 20763; do \
    echo JOB=\${job}; \
    tail -n 8 slurm-polysight-train-\${job}.out; \
  done
"
# Opción 2: Documento incrustado (Here-Doc)
ssh -F /home/chris/.ssh/config cedia 'bash -s' << 'EOF'
  cd ~/projects/polysight || exit 1
  
  sacct -j 20759,20760,20761,20762,20763 \
    --format=JobID,State,ExitCode,Elapsed,TotalCPU,MaxRSS -n -P
    
  for job in 20759 20760 20761 20762 20763; do
    echo "JOB=${job}"
    tail -n 8 "slurm-polysight-train-${job}.out"
  done
EOF
###

```

## Matriz de confusion, MLflow
```bash
# Sí. Nuestro pipeline guarda la matriz de confusión como artefacto PNG dentro de cada run de MLflow.
# Para verla:
# 1. Sincroniza los resultados recientes:

cd ~/projects/polysight
scripts/cluster/sync-results.sh

# 2. Inicia MLflow:
cd artifacts/cedia/mlflow

uvx mlflow ui \
--backend-store-uri sqlite:///mlflow.db \
--default-artifact-root ./artifacts \
--port 5000

# 3. Abre http://127.0.0.1:5000.
# 4. Entra al experimento polysight-main16.
# 5. Selecciona un run y navega a:
# Artifacts → validation → confusion-matrix.png

# En esa misma carpeta encontrarás:
# - metrics.json
# - per-class-metrics.csv
# - confusion-matrix.png

# MLflow permite visualizar la imagen individual de cada run. Sin embargo, la interfaz no compara automáticamente varias matrices de confusión lado a lado; habría que abrir
# cada run o crear posteriormente un reporte comparativo.
#
# La matriz generada por PolySight está normalizada por clase verdadera: cada fila muestra cómo se distribuyen las predicciones de una clase real. La diagonal representa
# aciertos; valores fuera de la diagonal muestran qué clases se están confundiendo.
```

## Capas Convolucionales y cabeza clasificadora
El proyecto no implementa manualmente las convoluciones. Utiliza EfficientNet-B0 de torchvision.

El punto de entrada está en src/polysight/model.py:12:

model = efficientnet_b0(weights=weights)

Las capas convolucionales están dentro de model.features, implementadas por torchvision.models.efficientnet_b0. PolySight únicamente reemplaza la cabeza clasificadora:

```bash
model.classifier = nn.Sequential(
    nn.Dropout(p=dropout),
    nn.Linear(in_features, num_classes),
)
```
Por tanto:

- model.features: convoluciones y bloques MBConv de EfficientNet-B0.
- model.avgpool: agrupación global.
- model.classifier: capa personalizada para 16 o 23 clases.
- freeze_backbone() congela o libera las convoluciones durante las dos etapas de entrenamiento.

El código fuente detallado de las convoluciones pertenece al paquete instalado:

torchvision/models/efficientnet.py

Puedes imprimir toda la arquitectura en un entorno con PyTorch mediante:

```python
from polysight.model import build_model

model = build_model(16, pretrained=False)
print(model.features)
```
En PolySight no aparece ningún nn.Conv2d porque esas capas son creadas internamente por efficientnet_b0().

## Y esto es entrenamiento por refuerzo?
No. PolySight usa aprendizaje supervisado para clasificación de imágenes, no aprendizaje por refuerzo.

Durante el entrenamiento:

1. Cada imagen viene acompañada por una etiqueta correcta.
2. EfficientNet-B0 genera probabilidades para 16 o 23 clases.
3. Se compara la predicción con la etiqueta mediante:
    - cross_entropy para baseline.
    - weighted_cross_entropy para weighted.

4. El error se propaga hacia atrás con backpropagation.
5. El optimizador actualiza los parámetros de la red.

Además, usamos transferencia de aprendizaje:

- EfficientNet-B0 comienza con pesos preentrenados en ImageNet.
- Primero se congela el backbone convolucional y se entrena la cabeza.
- Después se libera el backbone y se realiza fine-tuning.

En aprendizaje por refuerzo habría un agente, un entorno, acciones y recompensas. Aquí no existen esos componentes: tenemos imágenes etiquetadas y una función de pérdida
conocida. Por tanto, la descripción correcta es:

> Clasificación multiclase mediante aprendizaje supervisado y transferencia de aprendizaje con EfficientNet-B0.

## Y si quisiera crear mi propia arquitectura CNN?
• Sí, puedes crear una CNN propia. En PolySight implicaría reemplazar o complementar EfficientNet-B0 en src/polysight/model.py:12.

Por ejemplo, una arquitectura sencilla:
```python
class PolySightCNN(nn.Module):
    def __init__(self, num_classes: int, dropout: float = 0.2):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(256, num_classes),
        )

    def forward(self, images):
        features = self.features(images)
        return self.classifier(features)

Después build_model() seleccionaría la arquitectura indicada en el YAML:

def build_model(
    num_classes: int,
    architecture: str,
    dropout: float = 0.2,
) -> nn.Module:
    if architecture == "polysight_cnn":
        return PolySightCNN(num_classes, dropout)

    if architecture == "efficientnet_b0":
        # Construcción actual de EfficientNet
        ...

    raise ValueError(f"Arquitectura desconocida: {architecture}")
```

Y la configuración sería:

model:
architecture: polysight_cnn
pretrained: false
dropout: 0.2

Hay una diferencia experimental importante:

- EfficientNet usa transferencia de aprendizaje desde ImageNet.
- Una CNN propia normalmente comenzaría con pesos aleatorios.
- Con solo 10 662 imágenes etiquetadas, una arquitectura propia podría sobreajustarse o rendir menos que EfficientNet.
- Entrenarla permitiría aprender directamente cómo funcionan convoluciones, pooling, normalización y profundidad de red.

También habría que adaptar el entrenamiento actual. freeze_backbone() y las etapas de cabeza/fine-tuning están diseñadas para transferencia de aprendizaje. Para una CNN
desde cero sería preferible entrenar toda la red desde la primera época y posiblemente usar más regularización y data augmentation.

La comparación científicamente justa sería añadir una fase futura:

1. Diseñar PolySightCNN.
2. Probar dimensiones con un tensor artificial.
3. Contar parámetros.
4. Crear una configuración separada.
5. Entrenar con las mismas tres semillas y splits.
6. Comparar macro-F1, estabilidad, tiempo, RAM y GPU contra EfficientNet-B0.

No conviene incorporarla ahora a la cadena activa: primero debemos cerrar y evaluar los experimentos actuales. Luego puede añadirse al backlog como una comparación de
arquitectura propia frente a transferencia de aprendizaje.

## Lanzar MLflow localmente
```bash
# con ruta absolutas
# Desde la raíz del proyecto, usa:

uvx mlflow ui \
--backend-store-uri sqlite:////home/chris/projects/polysight/artifacts/cedia/mlflow/mlflow.db \
--default-artifact-root /home/chris/projects/polysight/artifacts/cedia/mlflow/artifacts \
--host 127.0.0.1 \
--port 5000

# O con rutas relativas:
cd ~/projects/polysight/artifacts/cedia/mlflow

uvx mlflow ui \
--backend-store-uri sqlite:///mlflow.db \
--default-artifact-root ./artifacts \
--host 127.0.0.1 \
--port 5000

# Ambos comandos son equivalentes. En la URI absoluta de SQLite se usan cuatro barras:
# sqlite:////home/...

# ruta relativa de SQLite: sqlite:///mlflow.db
# ejecutar el servidor con el proxy de artefactos habilitado:
cd ~/projects/polysight/artifacts/cedia/mlflow
#
uvx mlflow server \
--backend-store-uri sqlite:///mlflow.db \
--serve-artifacts \
--artifacts-destination ./artifacts \
--host 127.0.0.1 \
--port 5000

# ruta absoluta
uvx mlflow server \
--backend-store-uri sqlite:////home/chris/projects/polysight/artifacts/cedia/mlflow/mlflow.db \
--serve-artifacts \
--artifacts-destination /home/chris/projects/polysight/artifacts/cedia/mlflow/artifacts \
--host 127.0.0.1 \
--port 5000
```

# Resumen de resultados, directorios, artefactos, matrices de confusión y métricas
Los resultados están organizados así:

- Informe principal y conclusiones: docs/results.md
- Explicación didáctica: docs/testing-summary.md
- Comparación de los nueve entrenamientos: experiments/summary.csv
- Evaluaciones finales seleccionadas: experiments/final-evaluation.yaml
- Detalles de cada ejecución: experiments/runs

Resultados finales de cada modelo:

- artifacts/cedia/final-evaluation-derived/main16-baseline-seed42
- artifacts/cedia/final-evaluation-derived/full23-baseline-seed2026

Dentro de esas dos carpetas encontrarás:

- metrics.json: métricas generales.
- per-class-metrics.csv: precisión, recall y F1 por clase.
- confusion-matrix.csv: conteos exactos.
- confusion-matrix-normalized-readable.png: matriz visual más legible.
- confusion-matrix.png: matriz original.

Para empezar a leerlos, recomiendo abrir primero docs/results.md y después las matrices normalized-readable.png.

La copia local completa de MLflow está en artifacts/cedia/mlflow. Su interfaz se inicia desde esa carpeta con:
```bash
uvx mlflow ui \
--backend-store-uri sqlite:///mlflow.db \
--default-artifact-root ./artifacts \
--port 5000
```


## Imágenes por clase en split training
```bash
# en el cluster de CEDIA
[christian.bueno__espol.edu.ec@login1 ~]$ ll projects/polysight-storage/manifests/
total 0
drwxrwxr-x 2 christian.bueno__espol.edu.ec christian.bueno__espol.edu.ec 120 Aug  5 01:10 full23
drwxrwxr-x 2 christian.bueno__espol.edu.ec christian.bueno__espol.edu.ec 120 Aug  5 01:08 main16
[christian.bueno__espol.edu.ec@login1 ~]$ 

# revisar este archivo para ver cuántas imágenes hay por clase en el split de entrenamiento
cat projects/polysight-storage/manifests/main16/summary.json
```

Del `summary.json` que compartiste, el desglose por clase en el perfil **main16** (10.479 imágenes totales, 16 clases) es:

| Clase | Imágenes |
|---|---|
| bbps-2-3 | 1148 |
| polyps | 1028 |
| cecum | 1009 |
| dyed-lifted-polyps | 1002 |
| pylorus | 999 |
| dyed-resection-margins | 989 |
| z-line | 932 |
| retroflex-stomach | 764 |
| bbps-0-1 | 646 |
| retroflex-rectum | 391 |
| esophagitis-a | 403 |
| ulcerative-colitis-grade-2 | 443 |
| esophagitis-b-d | 260 |
| ulcerative-colitis-grade-1 | 201 |
| ulcerative-colitis-grade-3 | 133 |
| impacted-stool | 131 |

Ordenado de mayor a menor, se ve claramente el desbalance que mencionaste antes como justificación para usar macro-F1 y weighted cross-entropy: la clase más grande (`bbps-2-3`, 1148) tiene casi **9x** más imágenes que la más pequeña (`impacted-stool`, 131).

Si quieres, puedo calcular la proporción exacta de cada clase dentro del split de test (1571 imágenes) para ver si el desbalance se mantiene proporcional ahí también:

```bash
tail -n +2 projects/polysight-storage/manifests/main16/manifest.csv | \
  awk -F',' '$4=="test"{print $2}' | sort | uniq -c | sort -rn
```

## El desbalance mantiene proporcionaloidad entre split Training y Testing
Sí, se mantiene casi perfectamente proporcional — lo cual es exactamente el comportamiento esperado, dado que `assign_splits()` en `split.py` hace el split **estratificado por clase** (calcula `_targets()` de forma independiente para cada label, no de forma global).

| Clase | % del dataset (10.479) | % del test (1.571) | Diferencia |
|---|---|---|---|
| bbps-0-1 | 6.17% | 6.18% | +0.01 pp |
| bbps-2-3 | 10.96% | 10.95% | −0.01 pp |
| cecum | 9.63% | 9.61% | −0.02 pp |
| dyed-lifted-polyps | 9.56% | 9.55% | −0.01 pp |
| dyed-resection-margins | 9.44% | 9.42% | −0.02 pp |
| esophagitis-a | 3.85% | 3.82% | −0.03 pp |
| esophagitis-b-d | 2.48% | 2.48% | 0.00 pp |
| impacted-stool | 1.25% | 1.27% | +0.02 pp |
| polyps | 9.81% | 9.80% | −0.01 pp |
| pylorus | 9.53% | 9.55% | +0.02 pp |
| retroflex-rectum | 3.73% | 3.76% | +0.03 pp |
| retroflex-stomach | 7.29% | 7.32% | +0.03 pp |
| ulcerative-colitis-grade-1 | 1.92% | 1.91% | −0.01 pp |
| ulcerative-colitis-grade-2 | 4.23% | 4.20% | −0.03 pp |
| ulcerative-colitis-grade-3 | 1.27% | 1.27% | 0.00 pp |
| z-line | 8.90% | 8.91% | +0.01 pp |

**Máxima desviación: ±0.03 puntos porcentuales** — prácticamente ruido de redondeo (`_targets()` usa `round()`, que introduce el único error posible por clase, ±1 imagen).

**Conclusión:** el desbalance original de clases (9x entre `bbps-2-3`/`polyps` y `impacted-stool`) **se preserva íntegramente** en el split de test. Esto confirma que:

1. La estratificación funciona correctamente — ninguna clase quedó sub- o sobre-representada en test respecto al dataset completo.
2. La métrica de test que reportas (macro-F1) evalúa sobre una distribución fiel a la realidad del dataset, no sesgada por el split.
3. El bajo desempeño que ves en clases minoritarias como `impacted-stool` (recall 0.6, F1 0.706 en tu captura) o `ulcerative-colitis-grade-1` (recall 0.43, F1 0.52) **no es un artefacto del split** — es un problema genuino de pocos ejemplos de entrenamiento (131 y 201 imágenes totales respectivamente), justo el tipo de caso que la weighted cross-entropy busca mitigar.

## Cómo usamos los datos de validation

Los datos de `validation` se utilizan al final de cada época para examinar el
modelo, pero no para enseñarle directamente. Una época en PolySight funciona así:

```text
1. Entrenamiento con train
   -> el modelo hace predicciones
   -> se calcula el error
   -> backpropagation modifica los pesos

2. Evaluación con validation
   -> el modelo hace predicciones
   -> se calculan las métricas
   -> no se ejecuta backpropagation
   -> no se modifican los pesos
```

Al finalizar cada época, el modelo procesa todas las imágenes de `validation` y se
calculan accuracy, balanced accuracy, macro-F1, weighted-F1 y top-3 accuracy. La
métrica principal para tomar decisiones es macro-F1, porque asigna la misma
importancia a cada clase y resulta más informativa que accuracy cuando existen clases
desbalanceadas.

Por ejemplo:

| Época | Error en train | Macro-F1 validation | Acción |
|---:|---:|---:|---|
| 1 | 0.80 | 0.65 | Guardar el modelo |
| 2 | 0.55 | 0.74 | Reemplazar el modelo guardado |
| 3 | 0.40 | 0.81 | Reemplazar el modelo guardado |
| 4 | 0.28 | 0.80 | No reemplazarlo |
| 5 | 0.18 | 0.76 | No reemplazarlo |

Aunque el error de entrenamiento continúa bajando, el rendimiento de validation
empieza a empeorar después de la época 3. Esto puede indicar sobreajuste: el modelo
aprende detalles particulares de `train` que no se trasladan bien a imágenes no
utilizadas para ajustar sus pesos. En este ejemplo se conserva el modelo de la época
3, no el de la última época.

En PolySight, `validation` se usa para:

1. Guardar como `best.pt` el checkpoint con mayor macro-F1 de validation.
2. Decidir cuándo detener el entrenamiento mediante early stopping.
3. Comparar estrategias como `baseline` y `weighted` utilizando el macro-F1 promedio
   de tres semillas.
4. Elegir el modelo que posteriormente se evalúa una sola vez sobre `test`.

Aunque validation no modifica directamente los pesos, sí influye indirectamente en
la elección del modelo. Por eso `test` se mantiene separado y no se utiliza para tomar
estas decisiones:

```text
Train      -> ajusta los pesos
Validation -> elige cómo y hasta cuándo entrenar
Test       -> evalúa finalmente la elección completa
```

## Early stopping y su lugar en el entrenamiento

Early stopping interviene durante el entrenamiento, inmediatamente después de
evaluar el modelo con `validation` al final de cada época:

```text
Entrenar una época con train
            ->
Evaluar el modelo con validation
            ->
Comparar macro-F1 con el mejor valor anterior
            ->
¿Mejoró?
  Sí -> guardar best.pt y reiniciar el contador
  No -> aumentar el contador de paciencia
            ->
¿Llegó a 7 épocas sin mejora durante fine-tuning?
  Sí -> detener el entrenamiento
  No -> comenzar la siguiente época
```

PolySight tiene dos etapas de entrenamiento:

1. **Entrenamiento de la cabeza:** tres épocas con el backbone de EfficientNet-B0
   congelado.
2. **Fine-tuning:** hasta 30 épocas con el backbone descongelado.

El contador se actualiza después de cada evaluación, pero la detención anticipada solo
puede cortar el proceso durante la etapa de fine-tuning. La paciencia configurada es
de siete épocas consecutivas sin superar el mejor macro-F1 anterior.

Por ejemplo:

| Época | Macro-F1 validation | Mejor hasta ahora | Contador |
|---:|---:|---:|---:|
| 10 | 0.78 | 0.78 | 0 |
| 11 | 0.81 | 0.81 | 0 |
| 12 | 0.80 | 0.81 | 1 |
| 13 | 0.79 | 0.81 | 2 |
| 14 | 0.805 | 0.81 | 3 |
| 15 | 0.80 | 0.81 | 4 |
| 16 | 0.79 | 0.81 | 5 |
| 17 | 0.78 | 0.81 | 6 |
| 18 | 0.80 | 0.81 | 7: detener |

En este caso, el entrenamiento termina en la época 18, pero el modelo elegido es el
de la época 11, porque obtuvo el mejor macro-F1 de validation. Por tanto, son dos
decisiones relacionadas pero diferentes:

- **Early stopping** decide cuándo dejar de entrenar.
- **`best.pt`** identifica qué versión del modelo se conserva.

No se detiene tras una sola época peor porque las métricas pueden fluctuar. La
paciencia permite que el modelo atraviese descensos temporales y todavía pueda mejorar
después. El valor siete es una heurística aplicada consistentemente en el proyecto;
no se realizó una búsqueda sistemática que demuestre que sea el valor óptimo.
