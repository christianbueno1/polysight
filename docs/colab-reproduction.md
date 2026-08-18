# Reproducción de PolySight en Google Colab

## Propósito

Los notebooks de `notebooks/` permiten comprobar el modelo final y repetir el
entrenamiento principal sin copiar la implementación de `src/polysight/` dentro de
celdas. Cada notebook clona una referencia Git explícita e instala el paquete real.
El notebook principal ejecuta las pruebas y muestra con `inspect.getsource` las
funciones centrales realmente importadas, de modo que el código puede revisarse desde
Colab sin crear una segunda implementación.

## Notebooks

### Verificación por inferencia

`01-polysight-inference-verification.ipynb` carga el checkpoint final
`main16-baseline-seed42`, verifica su SHA-256 y produce el top-3 para una imagen subida
por la persona que ejecuta el notebook.

Esta prueba es corta y demuestra que el artefacto puede cargarse y generar inferencias
fuera de CEDIA. No repite el entrenamiento ni evalúa calidad clínica.

### Reproducción de entrenamiento

`02-polysight-training-reproduction.ipynb` ejecuta:

1. verificación de Python y montaje de Google Drive;
2. checkout del commit original de `main16-baseline-seed42`;
3. instalación del paquete y ejecución de Pytest y Ruff;
4. inspección del código fuente importado para datos, modelo, entrenamiento y métricas;
5. diagnóstico de GPU, PyTorch, Torchvision y MLflow;
6. verificación del ZIP, pesos iniciales y checkpoint final;
7. preparación de datos y comparación del manifest con el hash auditado;
8. inferencia corta con el checkpoint final sobre una imagen de validation;
9. smoke test;
10. entrenamiento completo con semilla 42;
11. comparación de métricas de validation contra CEDIA;
12. exportación de MLflow, checkpoints, manifests y reporte a Drive.

La evaluación sobre test está desactivada por defecto. Solo debe habilitarse después
de cerrar cualquier decisión sobre entorno o ejecución, y el resultado no debe usarse
para ajustar el modelo.

## Entradas externas

Los siguientes archivos no se almacenan en Git y deben estar disponibles en Google
Drive:

```text
polysight-inputs/
├── hyper-kvasir-labeled-images.zip
├── efficientnet_b0_rwightman-7f5810bc.pth
└── main16-baseline-seed42-best.pt
```

El notebook valida el ZIP por tamaño y SHA-256. Para los pesos iniciales valida el
prefijo SHA-256 contenido en su nombre y registra el digest completo observado.

El checkpoint final usado por el notebook de inferencia puede obtenerse desde los
artefactos sincronizados de MLflow. Su SHA-256 esperado es:

```text
74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c
```

## Configuración antes de ejecutar

En ambos notebooks debe sustituirse:

```python
REPO_URL = "https://github.com/ORGANIZACION/polysight.git"
```

Si el repositorio es privado, el acceso debe configurarse mediante secretos o un
mecanismo temporal de autenticación de Colab. Nunca se debe guardar un token en el
archivo `.ipynb` ni confirmar credenciales en Git.

El notebook de entrenamiento presupone estas rutas de Drive:

```python
DRIVE_INPUT_DIR = Path("/content/drive/MyDrive/polysight-inputs")
DRIVE_OUTPUT_DIR = Path("/content/drive/MyDrive/polysight-colab-results")
```

Pueden modificarse antes de ejecutar el resto de las celdas.

## Python y dependencias

PolySight `0.1.0` declara Python `>=3.11,<3.12`. Los notebooks verifican la versión y
se detienen si el runtime no usa Python 3.11. No amplían silenciosamente la
compatibilidad del proyecto.

Colab puede actualizar su entorno base. Cada ejecución registra las versiones reales
de Python, PyTorch, Torchvision, MLflow, CUDA y cuDNN, además del modelo de GPU.

## Qué significa reproducir el experimento

La reproducción debe conservar:

- commit del código;
- dataset y manifest por SHA-256;
- pesos iniciales;
- perfil `main16` y estrategia baseline;
- semilla 42;
- transformaciones;
- batch size, épocas, learning rates, paciencia y loss;
- selección mediante macro-F1 de validation.

El checkpoint producido en Colab no tiene que coincidir byte por byte con el de CEDIA.
El entrenamiento mantiene `cudnn.benchmark=True` y puede usar GPU, drivers, CUDA, cuDNN
y kernels diferentes. La comparación válida se apoya en el protocolo, la trazabilidad
y métricas cercanas, no solamente en el hash final.

## Limitaciones operativas

- El runtime de Colab y su GPU no están garantizados permanentemente.
- La sesión puede interrumpirse y eliminar archivos de `/content`.
- El ZIP ocupa aproximadamente 3,9 GB y requiere espacio adicional al extraerse.
- Los resultados deben copiarse a Drive antes de cerrar la sesión.
- El experimento original usó una A100 de 40 GB; otro tipo de GPU puede producir tiempos
  y resultados numéricos diferentes.
- Reducir batch size, épocas o imágenes convierte la ejecución en otra configuración y
  debe declararse como tal.

## Validación local de los notebooks

Las pruebas comprueban que ambos archivos sean JSON válido, que el código de sus celdas
tenga sintaxis Python válida, que no guarden outputs y que conserven hashes, commit,
configuraciones y política de test esenciales:

```bash
pytest tests/test_colab_notebooks.py
```

Esta validación local no sustituye una ejecución completa en Colab. La aceptación
funcional mínima en Colab requiere que Pytest y Ruff terminen correctamente, que la
inferencia auditada produzca top-3 y que el smoke test cree un checkpoint. La repetición
experimental completa añade el entrenamiento `main16-baseline` y la comparación de
validation.
