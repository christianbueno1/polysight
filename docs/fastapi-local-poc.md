# Prueba local de la API FastAPI en una laptop

## Propósito

Esta guía define lo mínimo necesario para probar en una laptop una API FastAPI que
sirva el modelo final `main16` de PolySight. Complementa
`docs/fastapi-api-handoff.md`, que contiene el diseño general para el repositorio
independiente.

El objetivo de esta prueba de concepto es comprobar que:

- el checkpoint puede cargarse correctamente;
- el preprocesamiento coincide con PolySight;
- la API produce el mismo top-3 que `polysight-predict`;
- las entradas inválidas se rechazan de manera controlada;
- una laptop puede ejecutar el servicio con recursos razonables.

No es una prueba de producción, escalabilidad ni validación clínica.

## Arquitectura suficiente

```text
Laptop
├── proyecto FastAPI
├── entorno Python 3.11
├── checkpoint local best.pt
└── archivo de configuración o variables de entorno
```

La API carga directamente el checkpoint desde el sistema de archivos:

```text
FastAPI
  -> encuentra best.pt
  -> verifica su SHA-256
  -> construye EfficientNet-B0
  -> carga los pesos una sola vez
  -> marca /ready como disponible
  -> recibe imágenes mediante /predict
```

No es necesario ejecutar MLflow para este flujo.

## Modelo local

Usar el modelo final `main16-baseline-seed42`:

```text
SHA-256:
74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c
```

En PolySight, su copia local se encuentra en:

```text
artifacts/cedia/mlflow/artifacts/2/cb29daac69dd4c9aa8a31ca621d08613/artifacts/checkpoints/best.pt
```

En la laptop puede guardarse fuera del repositorio de la API, por ejemplo:

```text
~/models/polysight/
└── main16-baseline-seed42/
    ├── best.pt
    └── metadata.json
```

No se recomienda guardar el checkpoint de aproximadamente 47 MB dentro de Git.

Un `metadata.json` local puede registrar:

```json
{
  "name": "polysight-main16",
  "version": 1,
  "profile": "main16",
  "architecture": "efficientnet_b0",
  "sha256": "74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c",
  "source_run": "cb29daac69dd4c9aa8a31ca621d08613",
  "clinical_validation": false
}
```

## Dependencias mínimas

El nuevo proyecto necesita como base:

```toml
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "python-multipart",
  "pydantic-settings",
  "Pillow",
  "torch",
  "torchvision",
]
```

También necesita:

- Python 3.11;
- código de carga compatible con el checkpoint de PolySight;
- la misma transformación de imagen usada por `polysight-predict`;
- pruebas con `pytest` y el cliente de prueba de FastAPI.

Las versiones de PyTorch y torchvision deben fijarse después de verificar paridad con
el entorno de PolySight. El modelo debe construirse con `pretrained=False` para evitar
descargas de pesos durante el arranque.

## Configuración local sugerida

```env
POLYSIGHT_CHECKPOINT_PATH=/ruta/absoluta/modelos/main16-baseline-seed42/best.pt
POLYSIGHT_CHECKPOINT_SHA256=74aae659c028fc58a368f5a3f61a4c7875d1608a2cade0ade6da1ca5ebdb609c
POLYSIGHT_DEVICE=cpu
POLYSIGHT_TOP_K=3
POLYSIGHT_MAX_IMAGE_MB=10
POLYSIGHT_MAX_CONCURRENCY=1
```

Para la primera prueba se recomienda `POLYSIGHT_DEVICE=cpu`. Si posteriormente se
prueba una GPU compatible, puede usarse `auto` o `cuda`, pero la GPU no debe ser un
requisito para validar el funcionamiento de la API.

La aplicación debe negarse a declarar readiness si:

- no existe el checkpoint;
- no coincide su SHA-256;
- no puede reconstruirse la arquitectura;
- los pesos o metadatos son incompatibles.

## Arranque local

Ejecutar un solo proceso y escuchar únicamente en la interfaz local:

```bash
uv run uvicorn polysight_api.app:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 1
```

Usar `127.0.0.1` evita exponer accidentalmente la prueba a otros equipos de la red.
Un único worker evita cargar varias copias del modelo en RAM. El modo `--reload` puede
usarse durante desarrollo, pero cada recarga vuelve a cargar el checkpoint.

## Endpoints mínimos

| Método | Endpoint | Resultado esperado |
|---|---|---|
| `GET` | `/health` | El proceso HTTP está activo |
| `GET` | `/ready` | El checkpoint fue verificado y el modelo está cargado |
| `GET` | `/model` | Identidad, versión, clases y SHA-256 |
| `POST` | `/predict` | Top-3 para una imagen válida |

Ejemplo:

```bash
curl -X POST \
  -F "image=@imagen.jpg" \
  http://127.0.0.1:8000/predict
```

La respuesta debe incluir las predicciones ordenadas de mayor a menor, el tiempo de
procesamiento y una advertencia de que el modelo no está validado para uso clínico.

## Flujo de prueba recomendado

```text
1. Copiar best.pt fuera del repositorio de la API
2. Calcular y comparar su SHA-256
3. Configurar ruta, hash, CPU, top-k y límites
4. Arrancar FastAPI con un worker
5. Consultar /health
6. Consultar /ready
7. Consultar /model
8. Enviar una imagen válida a /predict
9. Ejecutar polysight-predict con la misma imagen
10. Comparar clases y probabilidades
11. Probar archivos corruptos y demasiado grandes
12. Reiniciar la API y repetir la predicción
```

La prueba de paridad es esencial: verifica que separar la API en otro repositorio no
cambió el orden RGB, resize, crop, normalización, arquitectura, clases ni softmax.

## Pruebas mínimas de aceptación

- `/health` devuelve `200` mientras el proceso está activo.
- `/ready` solo devuelve `200` después de cargar un modelo válido.
- `/model` muestra nombre, versión, perfil y SHA-256 correctos.
- `/predict` acepta una imagen válida y devuelve tres resultados.
- Las clases están ordenadas por probabilidad descendente.
- Las probabilidades están entre 0 y 1.
- Una imagen vacía o corrupta se rechaza de forma controlada.
- Un archivo superior al límite produce `413 Payload Too Large`.
- Un checkpoint inexistente o con hash incorrecto impide readiness.
- El modelo se carga una sola vez durante el arranque.
- La salida coincide con `polysight-predict` dentro de una tolerancia definida.
- Reiniciar la API produce el mismo resultado para la misma imagen.
- Las pruebas y la inferencia no necesitan acceso a Internet.
- Los logs no contienen los bytes ni el contenido de las imágenes.

## Qué medir en la laptop

Aunque no sea una prueba de carga, registrar:

- tiempo de arranque y carga del checkpoint;
- primera inferencia y siguientes inferencias por separado;
- memoria RAM antes y después de cargar el modelo;
- latencia de varias solicitudes secuenciales;
- uso de CPU;
- tamaño máximo de imagen aceptable;
- comportamiento ante dos solicitudes concurrentes.

La primera inferencia puede ser más lenta que las siguientes. No deben extraerse
conclusiones usando una sola medición.

## Componentes que no son necesarios

Para esta prueba local pueden omitirse:

- PostgreSQL;
- MinIO, S3 u otro almacenamiento de objetos;
- MLflow Model Registry remoto;
- servidor MLflow permanente;
- Docker o Podman;
- Kubernetes;
- Caddy o Nginx;
- dominio, DNS y TLS;
- balanceador de carga;
- varias réplicas o workers;
- GPU;
- autenticación;
- rate limiting externo;
- CI/CD de despliegue;
- Prometheus y Grafana;
- base de datos de solicitudes;
- almacenamiento de imágenes;
- colas y procesamiento asíncrono;
- rollout canary o pruebas A/B.

Estos componentes pueden ser necesarios más adelante, pero no ayudan a demostrar la
paridad y funcionamiento básico de la inferencia local.

## Uso opcional de MLflow local

MLflow local no es necesario para la primera prueba. El flujo preferido es:

```text
FastAPI -> checkpoint local best.pt
```

Si posteriormente se desea practicar el concepto de Registry, puede iniciarse la
copia local existente con SQLite y artefactos locales. Sin embargo, primero debe
registrarse formalmente el modelo final: actualmente los archivos están disponibles
como artefactos de MLflow, pero no existe una entrada en `registered_models`.

El Registry local debe tratarse como un segundo ejercicio. No conviene introducirlo
antes de comprobar que la inferencia directa es correcta.

## Criterio de terminado

La prueba local está completa cuando la API arranca en CPU con un checkpoint verificado,
responde los cuatro endpoints, coincide con `polysight-predict`, rechaza entradas
inválidas, funciona sin Internet y deja registradas sus mediciones básicas de latencia
y memoria.
