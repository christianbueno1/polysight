## Dataset SUN-SEG

- Archivo principal observado:
  `SUN-SEG-FinalData-v20251212.tar.gz`
- Tamaño del archivo: `22 GiB`
- Subconjunto contenido: positivos densamente anotados de SUN-SEG
- Frames positivos: `49.136`
- Anotaciones por frame: máscara `GT`, polígono, borde, scribble y caja
  delimitadora
- Dataset completo descrito por el repositorio: `158.690` frames
  - `49.136` positivos
  - `109.554` negativos
- Origen estructural: `113` videos recortados en `1.106` clips

## MLflow local

- Estos archivos son los que debemos sincronizar en local: `mlflow.db` y `artifacts/`; los archivos `.log` se excluyen durante la sincronización.
- La interfaz local puede iniciarse desde la carpeta copiada con:
  `uvx mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./artifacts --port 5000`.
- Los experimentos, runs y modelos guardan ubicaciones portables con el esquema `mlflow-artifacts:/`; no contienen rutas absolutas de artefactos de CEDIA.
- Ruta de los modelos, por ejemplo el modelo `m-5648115171ee4f6ca70936bf6079a484` está disponible localmente en
  `artifacts/1/models/m-5648115171ee4f6ca70936bf6079a484/artifacts/data/model.pt2`.
