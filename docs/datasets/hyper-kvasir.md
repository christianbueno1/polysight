## Dataset Hyper-Kvasir

- Origen local:
  `/home/chris/Downloads/hyper-kvasir-labeled-images.zip`
- Destino remoto:
  `/home/christian.bueno__espol.edu.ec/datasets/hyper-kvasir-labeled-images.zip`
- Tamaño verificado: `3,928,814,344` bytes
- SHA-256 verificado:
  `c603449b1bc0be86948b11d9aea8b2002058a11e6f5499e2a384b9ae9c8dbd3f`

El tamaño y el SHA-256 coinciden entre el archivo local y el remoto.

## Taxonomía y perfiles

El archivo contiene 10.662 imágenes etiquetadas en 23 clases. PolySight genera dos
perfiles sin modificar las imágenes originales:

- `main16`: 16 clases con al menos 100 imágenes; es el experimento principal.
- `full23`: las 23 clases; es exploratorio por la escasez extrema de algunas clases.

Las siete clases excluidas de `main16` son `barretts-short-segment` (53), `barretts`
(41), `ulcerative-colitis-grade-0-1` (35), `ulcerative-colitis-grade-2-3` (28),
`ulcerative-colitis-grade-1-2` (11), `ileum` (9) y `hemorrhoids` (6).

## Preparación

```bash
polysight-prepare \
  --archive /home/chris/Downloads/hyper-kvasir-labeled-images.zip \
  --output-dir data/hyper-kvasir

polysight-split --data-dir data/hyper-kvasir --output-dir manifests --profile main16
polysight-split --data-dir data/hyper-kvasir --output-dir manifests --profile full23
```

Los manifests usan un split estratificado determinista 70/15/15. Los duplicados
exactos permanecen juntos y `perceptual-duplicates.json` identifica pares potenciales
mediante dHash para revisión. HyperKvasir no incluye identificadores suficientes para
garantizar separación por paciente o procedimiento; esta limitación debe aparecer en
todo reporte experimental.

