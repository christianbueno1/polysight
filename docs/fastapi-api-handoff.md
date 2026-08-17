# Guía de traspaso para la API de inferencia FastAPI

## Propósito

Esta guía sirve como contexto inicial para crear, en un repositorio independiente,
una API HTTP que exponga inferencias del modelo final de PolySight.

La separación recomendada es:

- **PolySight:** preparación de datos, entrenamiento, evaluación, trazabilidad y
  selección de modelos.
- **Nuevo proyecto FastAPI:** carga de un modelo ya seleccionado, validación de
  solicitudes, inferencia, contrato HTTP, observabilidad y despliegue.

La API no debe entrenar modelos, volver a comparar checkpoints ni utilizar los datos
de train, validation o test. Su entrada es una imagen proporcionada por el cliente y
su salida es una predicción del modelo congelado.

## Modelo recomendado para la primera versión

Usar solamente el modelo final `main16-baseline-seed42`:

| Campo | Valor |
|---|---|
| Arquitectura | EfficientNet-B0 |
| Perfil | `main16` (16 clases) |
| Estrategia | Baseline, cross-entropy |
| Semilla | 42 |
| Run MLflow | `cb29daac69dd4c9aa8a31ca621d08613` |
| Macro-F1 validation | `0.8583948872106766` |
| Macro-F1 test | `0.8521002634453307` |
| Accuracy test | `0.9191597708465945` |
| SHA-256 del checkpoint | `74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c` |
| Tamaño aproximado | 47 MB |

En la copia local de PolySight, el checkpoint se encuentra en:

```text
artifacts/cedia/mlflow/artifacts/2/cb29daac69dd4c9aa8a31ca621d08613/artifacts/checkpoints/best.pt
```

La ruta anterior es una referencia de procedencia, no una ruta que deba quedar
codificada en la API. El nuevo proyecto debe recibir la ubicación del checkpoint por
configuración y verificar su SHA-256 al iniciar.

La selección oficial y sus resultados están documentados en:

- `experiments/final-evaluation.yaml`
- `docs/results.md`
- `docs/traceability.md`
- `docs/testing-summary.md`

No se recomienda exponer inicialmente `full23`: su accuracy test fue alta, pero su
macro-F1 fue `0.6121377118735469` y seis clases obtuvieron F1 cero.

## Código de PolySight que debe conocerse

El punto de partida de inferencia es `src/polysight/predict.py`. Actualmente su función
`predict()` realiza en una sola llamada:

1. selección de CPU o CUDA;
2. lectura de `best.pt`;
3. recuperación de clases y configuración desde el checkpoint;
4. construcción de EfficientNet-B0;
5. carga de los pesos;
6. aplicación de la transformación de test;
7. cálculo de softmax y top-3.

La API no debe ejecutar los pasos 2 a 6 completos en cada solicitud. Debe extraer o
adaptar esa lógica a un servicio de inferencia que cargue el checkpoint, el modelo y
la transformación una sola vez durante el arranque.

Archivos relevantes:

- `src/polysight/predict.py`: flujo actual de predicción top-1/top-3.
- `src/polysight/model.py`: construcción de EfficientNet-B0 y cabeza clasificadora.
- `src/polysight/data/dataset.py`: transformaciones usadas en test.

El agente del nuevo proyecto debe decidir cómo consumir esta lógica sin acoplar la API
al repositorio completo. Alternativas razonables:

1. instalar una versión publicada del paquete `polysight`;
2. extraer una librería de inferencia versionada y pequeña;
3. implementar el cargador en el nuevo repositorio con pruebas de paridad contra la
   CLI de PolySight.

No se recomienda copiar archivos informalmente sin registrar la versión o commit de
origen. Cualquier implementación debe probar que, para una misma imagen y checkpoint,
produce las mismas clases y probabilidades que `polysight-predict`.

## Arquitectura inicial recomendada

```text
Nuevo repositorio
├── pyproject.toml
├── README.md
├── src/
│   └── polysight_api/
│       ├── __init__.py
│       ├── app.py
│       ├── routes.py
│       ├── schemas.py
│       ├── settings.py
│       └── inference.py
└── tests/
    ├── test_api.py
    └── test_inference.py
```

Responsabilidades:

- `app.py`: crear FastAPI y gestionar el ciclo de vida de la aplicación.
- `inference.py`: cargar y mantener el modelo en memoria; ejecutar predicciones.
- `routes.py`: definir los endpoints sin contener lógica de PyTorch.
- `schemas.py`: modelos Pydantic para respuestas y metadatos.
- `settings.py`: configuración mediante variables de entorno.

## Ciclo de vida del modelo

Usar el mecanismo `lifespan` de FastAPI:

```text
Arranque
  -> validar configuración
  -> verificar existencia y SHA-256 del checkpoint
  -> elegir dispositivo
  -> construir el modelo
  -> cargar los pesos
  -> activar modo eval
  -> preparar transformaciones
  -> marcar la API como lista

Solicitud
  -> validar imagen
  -> transformar
  -> ejecutar inference_mode
  -> calcular top-k
  -> responder

Apagado
  -> liberar referencias y recursos si corresponde
```

No cargar el modelo dentro del endpoint. Tampoco usar múltiples workers de servidor
sin medir su impacto: cada proceso puede mantener su propia copia del modelo en RAM o
VRAM.

## Contrato HTTP inicial

| Método | Endpoint | Propósito |
|---|---|---|
| `GET` | `/health` | Indicar que el proceso HTTP está activo |
| `GET` | `/ready` | Indicar que el modelo fue cargado y está disponible |
| `GET` | `/model` | Exponer identidad, perfil, clases, versión y hash del modelo |
| `POST` | `/predict` | Recibir una imagen y devolver las tres clases más probables |

Solicitud de ejemplo:

```bash
curl -X POST \
  -F "image=@imagen.jpg" \
  http://localhost:8000/predict
```

Respuesta sugerida:

```json
{
  "model": "main16-baseline-seed42",
  "predictions": [
    {"class": "polyps", "probability": 0.9234},
    {"class": "dyed-lifted-polyps", "probability": 0.0512},
    {"class": "dyed-resection-margins", "probability": 0.0128}
  ],
  "processing_time_ms": 84.3,
  "warning": "Resultado experimental; no está validado para uso clínico."
}
```

El esquema debe usar nombres estables y probabilidades numéricas entre 0 y 1,
ordenadas de mayor a menor. La advertencia clínica debe estar presente en la respuesta
o quedar incorporada de forma inequívoca en el contrato y la interfaz consumidora.

## Configuración sugerida

```env
POLYSIGHT_CHECKPOINT_PATH=/models/main16-best.pt
POLYSIGHT_CHECKPOINT_SHA256=74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c
POLYSIGHT_DEVICE=auto
POLYSIGHT_TOP_K=3
POLYSIGHT_MAX_IMAGE_MB=10
POLYSIGHT_MAX_CONCURRENCY=1
```

- `POLYSIGHT_DEVICE=auto` selecciona CUDA cuando está disponible y CPU en caso
  contrario.
- `POLYSIGHT_TOP_K` nunca debe superar el número de clases del checkpoint.
- El límite de concurrencia debe medirse y ajustarse según CPU, RAM, GPU y VRAM.
- No registrar imágenes ni contenido sensible por defecto.

## Validación de solicitudes y seguridad básica

El endpoint `/predict` debe:

- limitar el tamaño del cuerpo y del archivo;
- aceptar solo formatos explícitamente soportados;
- comprobar el contenido real con Pillow, no solo extensión o `Content-Type`;
- rechazar imágenes vacías, truncadas o corruptas;
- normalizar toda imagen a RGB mediante la misma transformación del modelo;
- evitar guardar temporalmente la imagen salvo que sea estrictamente necesario;
- controlar concurrencia para no saturar el modelo;
- devolver errores consistentes sin revelar rutas internas ni trazas.

Si la API queda expuesta fuera de una red confiable, deben añadirse autenticación,
TLS, rate limiting, límites en el proxy y políticas CORS explícitas. FastAPI no debe
interpretarse por sí solo como una frontera de seguridad completa.

## Dependencias iniciales

Como base:

```toml
dependencies = [
  "fastapi",
  "pydantic-settings",
  "python-multipart",
  "uvicorn[standard]",
  "Pillow",
  "torch",
  "torchvision",
]
```

Las versiones deben fijarse de manera compatible con el artefacto y el entorno donde
se validó la inferencia. Antes de decidir versiones, el agente debe inspeccionar el
lockfile o entorno de PolySight y ejecutar pruebas de paridad. No debe permitirse que
torchvision intente descargar pesos: el checkpoint contiene el estado entrenado y el
modelo debe construirse con `pretrained=False`.

## Pruebas mínimas de aceptación

1. El modelo se carga una sola vez al arrancar.
2. `/health` distingue vida del proceso de disponibilidad del modelo.
3. `/ready` falla mientras no exista un modelo válido.
4. `/model` devuelve el hash esperado y las 16 clases del checkpoint.
5. Una imagen válida devuelve tres predicciones ordenadas.
6. Todas las probabilidades están entre 0 y 1.
7. Imagen corrupta, vacía o no soportada produce un error controlado.
8. Un archivo mayor al límite produce `413 Payload Too Large`.
9. Un checkpoint ausente, corrupto o con hash distinto impide declarar readiness.
10. La salida coincide, dentro de una tolerancia definida, con `polysight-predict`.
11. Las pruebas no descargan pesos ni requieren acceso a Internet.
12. Los logs no contienen bytes de la imagen ni datos sensibles.

Conviene incluir una imagen de prueba redistribuible o sintética y un resultado dorado
para verificar la paridad. No copiar una imagen de HyperKvasir sin revisar primero sus
condiciones de redistribución.

## Observabilidad recomendada

Registrar como mínimo:

- identificador de solicitud;
- código de respuesta;
- tiempo total e inferencia en milisegundos;
- dispositivo utilizado;
- identidad y hash del modelo;
- errores de validación, sin incluir el contenido de la imagen.

Las probabilidades y clases predichas pueden ser datos sensibles en un contexto real;
no deben registrarse por defecto. Las métricas operativas futuras pueden incluir
latencia, cantidad de solicitudes, errores y saturación, evitando etiquetas de alta
cardinalidad.

## Fuera del alcance de la primera versión

- entrenamiento o fine-tuning;
- selección dinámica entre experimentos;
- evaluación sobre train, validation o test;
- escritura en MLflow por cada solicitud;
- almacenamiento de imágenes;
- procesamiento por lotes;
- Grad-CAM u otras explicaciones;
- soporte inicial para `full23`;
- afirmaciones de diagnóstico o validación clínica.

## Orden de implementación sugerido

1. Crear el repositorio, `pyproject.toml`, entorno y pruebas base.
2. Definir configuración tipada y verificación SHA-256.
3. Implementar el servicio de inferencia con carga única.
4. Crear una prueba de paridad con `polysight-predict`.
5. Implementar `/health`, `/ready` y `/model`.
6. Implementar `/predict` y validación estricta de imágenes.
7. Agregar pruebas de errores, tamaño y concurrencia.
8. Medir latencia y memoria en CPU y, si corresponde, GPU.
9. Crear contenedor no privilegiado y health checks.
10. Documentar ejecución local, configuración, contrato y limitaciones.

## Decisiones que debe confirmar el responsable del nuevo proyecto

Antes de desplegar, confirmar:

- entorno objetivo: desarrollo local, servidor interno o servicio público;
- CPU o GPU y presupuesto de memoria;
- mecanismo autorizado para entregar y versionar el checkpoint;
- necesidad de autenticación y usuarios consumidores;
- volumen y concurrencia esperados;
- formatos y tamaños de imagen permitidos;
- política de retención y privacidad;
- necesidad de contenedor, proxy inverso, TLS y monitoreo;
- licencia y condiciones de redistribución del código, checkpoint y datos de prueba.

## Criterio de terminado para la primera versión

La primera versión está lista cuando puede arrancar con un checkpoint configurado,
verificar su identidad, responder health/readiness, procesar una imagen válida con el
mismo resultado que la CLI de PolySight, rechazar entradas inválidas de forma segura y
ejecutar sus pruebas sin red ni acceso al dataset experimental.
