## revisar job
```bash
squeue -j 20735 -o "%i|%T|%M|%R"; sacct -j 20735 --format=JobID,State,Elapsed,ExitCode -n -P 2>/dev/null || true; tail -n 35 slurm-polysight-bootstrap-20735.out 2>/dev/null || true

|# run jobs
sbatch slurm/bootstrap.sbatch
sbatch slurm/diagnose.sbatch
sbatch slurm/prepare-data.sbatch
sbatch slurm/smoke.sbatch

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