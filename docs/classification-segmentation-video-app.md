# Aplicación de clasificación y segmentación de video

## Visión general

La aplicación propuesta debe analizar imágenes o videos endoscópicos mediante dos
modelos diferentes y complementarios:

```text
Clasificación -> indica qué hallazgo aparece
Segmentación  -> indica qué píxeles pertenecen al pólipo
```

PolySight ya dispone del modelo de clasificación final `main16-baseline-seed42`. Para
completar la capacidad de segmentación falta preparar Kvasir-SEG, entrenar y evaluar el
segmentador, congelar su checkpoint y construir el pipeline audiovisual que combine
ambos resultados.

Por tanto, no falta solamente un segundo archivo de modelo. También hacen falta
decodificación de video, procesamiento de frames, composición gráfica, codificación del
resultado, control de trabajos largos y evaluación del sistema integrado.

## Responsabilidad del clasificador

El clasificador recibe el frame completo y produce probabilidades para las 16 clases:

```text
Frame del video
      -> EfficientNet-B0
      -> probabilidades por clase
      -> top-3
```

Ejemplo conceptual:

```json
{
  "class": "polyps",
  "probability": 0.923
}
```

Este resultado indica qué hallazgo parece estar presente, pero no localiza el pólipo
dentro de la imagen.

## Responsabilidad del segmentador

El segmentador recibe un frame RGB y produce un logit o probabilidad por píxel:

```text
Frame: alto x ancho x 3
          -> modelo de segmentación
          -> logits: alto-modelo x ancho-modelo x 1
          -> sigmoid
          -> mapa de probabilidades
```

Ejemplo simplificado:

```text
0.02  0.01  0.03  0.04
0.01  0.76  0.91  0.08
0.02  0.83  0.95  0.05
```

Cada valor expresa la probabilidad de que el píxel pertenezca al pólipo. Con un umbral
inicial de `0.5`:

```text
probabilidad < 0.5  -> fondo
probabilidad >= 0.5 -> pólipo
```

Se obtiene una máscara binaria:

```text
0 0 0 0
0 1 1 0
0 1 1 0
```

El umbral debe seleccionarse usando validation. Test no debe utilizarse para ajustarlo.

## Arquitectura funcional

```text
                         +-> clasificador main16 -> top-3
Imagen o frame de video -+
                         +-> segmentador -> mapa y máscara
                                      |
                                      v
                         combinador de resultados
                                      |
                                      v
                 respuesta JSON, imagen o video anotado
```

Los modelos deben mantenerse como componentes independientes, con versión, hash,
preprocesamiento y pruebas de paridad propios. La capa de aplicación combina resultados
sin modificar los checkpoints.

## Cómo se agrega la segmentación a un video

El modelo no escribe directamente sobre un archivo de video. La aplicación debe
descomponer el video en frames, inferir y crear un archivo nuevo:

```text
Abrir video original
        -> leer un frame
        -> conservar timestamp y dimensiones
        -> transformar para clasificación
        -> ejecutar clasificador
        -> transformar para segmentación
        -> ejecutar segmentador
        -> restaurar la máscara al tamaño original
        -> crear overlay y anotaciones
        -> escribir el frame de salida
        -> repetir hasta terminar
        -> cerrar y validar el video resultante
```

La máscara predicha normalmente tiene la resolución de entrada del segmentador. Debe
redimensionarse a las dimensiones originales usando una interpolación coherente con el
tipo de salida. Para una máscara binaria final conviene preservar clases; para un mapa
continuo de probabilidades puede interpolarse antes de aplicar el umbral.

## Overlay y presentación

Una presentación inicial puede combinar:

```text
frame original
    +
máscara coloreada semitransparente
    +
texto de clasificación y confianza
    =
frame anotado
```

Elementos posibles:

- máscara semitransparente;
- contorno del pólipo;
- bounding box derivado de la máscara;
- clase top-1 o top-3;
- confianza del clasificador;
- porcentaje del frame cubierto por la máscara;
- versión de los modelos;
- timestamp del frame.

Ejemplo conceptual:

```text
Hallazgo: polyps
Confianza: 92.3%
Área segmentada: 18.4%
[región del pólipo resaltada]
```

El video original debe conservarse sin modificaciones. El video anotado es un
artefacto derivado. Las máscaras que se guarden por separado deben usar un formato sin
pérdida como PNG, no JPEG.

## Formas de ejecutar ambos modelos

### Ejecución paralela o independiente

```text
Frame
  +-> clasificación
  +-> segmentación
```

Ventajas:

- permite medir cada modelo de forma independiente;
- un error del clasificador no impide que el segmentador encuentre un pólipo;
- simplifica el análisis de errores;
- evita elegir prematuramente un umbral de activación.

Desventaja:

- ejecuta ambos modelos para todos los frames y consume más recursos.

Esta es la estrategia recomendada durante desarrollo y evaluación.

### Segmentación condicionada por clasificación

```text
Frame
  -> clasificador
  -> ¿probabilidad de polyps supera el umbral?
       +-> sí: ejecutar segmentación
       +-> no: continuar
```

Ventaja:

- puede reducir cómputo.

Riesgo:

- un falso negativo del clasificador evita por completo la segmentación;
- los errores del primer modelo se propagan al segundo;
- el umbral introduce otra decisión que debe ajustarse con validation.

No debe adoptarse esta optimización sin comparar primero sensibilidad, latencia y costo
del sistema completo frente a la ejecución independiente.

## Video frame por frame y consistencia temporal

Los primeros modelos operan sobre imágenes independientes. No conocen los frames
anteriores ni posteriores. Esto puede producir parpadeo:

```text
Frame 100 -> pólipo detectado
Frame 101 -> no detectado
Frame 102 -> pólipo detectado
```

También puede cambiar bruscamente la forma de la máscara:

```text
Frame 100 -> máscara grande
Frame 101 -> máscara pequeña
Frame 102 -> máscara grande
```

Para una primera versión offline puede aceptarse el procesamiento independiente. En
una fase posterior pueden investigarse:

- promedio de probabilidades entre frames cercanos;
- suavizado temporal de máscaras;
- eliminación de detecciones aisladas;
- tracking del pólipo;
- optical flow;
- propagación de máscaras;
- modelos específicos para video.

Toda estabilización cambia la salida del modelo y debe evaluarse. Conviene conservar
las predicciones originales para auditoría y evitar que el suavizado oculte fallos.

## Imagen frente a video

La integración debe progresar primero con imágenes:

```text
Imagen
  -> clasificar
  -> segmentar
  -> verificar paridad de ambos modelos
  -> generar overlay
```

Solo después debe agregarse video:

```text
Video
  -> decodificar frames
  -> reutilizar el pipeline validado de imagen
  -> preservar tiempos, FPS y dimensiones
  -> codificar el resultado
```

Esto permite separar errores del modelo de errores introducidos por codecs, espacios
de color, resize o composición de video.

## Procesamiento offline

Para la primera versión de video se recomienda un trabajo asíncrono:

```text
Cliente sube video
      -> aplicación crea un job
      -> worker procesa frames
      -> aplicación informa progreso
      -> cliente descarga resultados
```

Un contrato conceptual podría ser:

```text
POST /video-jobs
GET  /video-jobs/{id}
POST /video-jobs/{id}/cancel
GET  /video-jobs/{id}/result
```

El procesamiento no debe mantenerse abierto dentro de una solicitud HTTP larga. Se
necesitan estados como `queued`, `running`, `completed`, `failed` y `cancelled`, además
de limpieza de archivos temporales y una política de retención.

## Procesamiento en tiempo real

Tiempo real significa sostener el ritmo de entrada. Para un video de 30 FPS, el
presupuesto aproximado es:

```text
1 segundo / 30 frames = 33.3 ms por frame
```

Ese presupuesto incluye:

- decodificación;
- preprocesamiento;
- clasificación;
- segmentación;
- postprocesamiento;
- overlay;
- codificación o transmisión.

No debe afirmarse que el sistema funciona en tiempo real antes de medir el pipeline
completo sobre el hardware objetivo. Una implementación futura podría necesitar GPU,
resolución controlada, ejecución paralela, ONNX Runtime, TensorRT o muestreo de frames.

## Ejemplo de costo offline

Un video de diez minutos a 30 FPS contiene:

```text
30 x 60 x 10 = 18.000 frames
```

Si el pipeline conjunto tarda 100 ms por frame:

```text
18.000 x 0.1 segundos = 1.800 segundos = 30 minutos
```

Esta estimación muestra por qué la primera versión debe tratar el video como un trabajo
offline y medir antes de diseñar una solución en vivo.

## Resultados que puede producir la aplicación

Para una imagen:

- top-3 de clasificación;
- mapa de probabilidades;
- máscara binaria;
- overlay;
- bounding box derivado;
- identidad y hash de ambos modelos.

Para un video:

- video anotado;
- predicciones por frame;
- máscaras o referencias a máscaras;
- intervalos con detección de pólipo;
- estadísticas de confianza y área;
- tiempos de procesamiento;
- versiones exactas de modelos y configuración.

No conviene incluir cada máscara completa dentro de un único JSON grande. Los archivos
binarios deben almacenarse separadamente y el manifiesto debe referenciarlos.

## Qué falta para completar el sistema

1. Preparar Kvasir-SEG y generar splits auditables.
2. Implementar el pipeline de segmentación.
3. Entrenar varias semillas y seleccionar por Dice de validation.
4. Evaluar una sola vez sobre test.
5. Congelar y versionar `best.pt` del segmentador.
6. Implementar inferencia y postprocesamiento de máscaras.
7. Validar ambos modelos sobre imágenes.
8. Implementar decodificación y codificación de video.
9. Crear overlays reproducibles.
10. Implementar trabajos, progreso, cancelación y retención.
11. Medir CPU, RAM, GPU, VRAM, latencia y throughput.
12. Evaluar la interacción entre clasificación y segmentación.
13. Analizar consistencia temporal.
14. Documentar seguridad, privacidad y limitaciones clínicas.

## Evolución recomendada

```text
Versión 1 -> imagen: clasificación
Versión 2 -> imagen: segmentación
Versión 3 -> imagen: clasificación + segmentación + overlay
Versión 4 -> video offline frame por frame
Versión 5 -> estabilización temporal y optimización
Versión 6 -> evaluación de viabilidad en tiempo real
```

Cada versión debe conservar paridad con los modelos originales y añadir pruebas antes
de avanzar. No se debe comenzar por tiempo real, porque combinar modelos, codecs y
procesamiento temporal introduce demasiadas variables simultáneas.

## Consideraciones de evaluación

Los modelos deben evaluarse individualmente y como sistema:

```text
Clasificador -> macro-F1, recall de polyps y matriz de confusión
Segmentador  -> Dice, IoU, precision y recall por píxel
Sistema      -> sensibilidad del flujo, latencia y estabilidad temporal
```

Si se usa segmentación condicionada por clasificación, debe medirse cuántos pólipos se
pierden por falsos negativos del clasificador. Las métricas de cada modelo por separado
no describen completamente el comportamiento de la cascada.

## Alcance clínico y privacidad

Los modelos actuales son experimentales. Un overlay visual no constituye diagnóstico
ni validación clínica. Antes de usar videos reales deben definirse:

- autorización y base legal para procesarlos;
- eliminación de metadatos identificables;
- cifrado en tránsito y reposo;
- control de acceso;
- retención y eliminación;
- auditoría;
- revisión humana;
- evaluación prospectiva y externa.

La aplicación inicial debe presentarse como herramienta de investigación y no como
dispositivo o recomendación médica.
