# PHASE_CURRENT

## Fase 6 — Análisis final, documentación de resultados y release

**Objetivo:** Analizar los resultados cerrados sin volver a consultar test para ajustar
modelos, documentar conclusiones y limitaciones, y preparar un release reproducible.

**Contexto:** Ver `experiments/`, `artifacts/cedia/final-evaluation/`, `NOTES.md` y
`docs/cluster.md`.

---

### Tareas

- [x] Comparar métricas agregadas de main16 y full23
- [x] Analizar métricas por clase y matrices de confusión finales
- [x] Documentar rendimiento, estabilidad y consumo computacional
- [ ] Documentar conclusiones, limitaciones y amenazas a la validez
- [ ] Verificar trazabilidad de configuraciones, commits, manifests y artefactos
- [ ] Actualizar la documentación principal con resultados reproducibles
- [ ] Ejecutar validación final de pruebas, lint y estructura de artefactos
- [ ] Preparar y etiquetar el release estable

---

### Notas y decisiones

- Test quedó cerrado después de una única evaluación por perfil; no se ajustarán modelos
  ni hiperparámetros usando esos resultados.
- Modelos finales: main16 baseline semilla 42 y full23 baseline semilla 2026.
- Resultados consolidados en `experiments/summary.csv` y
  `experiments/final-evaluation.yaml`.
- Matrices y métricas por clase finales están sincronizadas bajo
  `artifacts/cedia/final-evaluation/` y permanecen fuera de Git.
- La comparación agregada está documentada en `docs/results.md`; separa promedios de
  validation (tres semillas) de la evaluación test única de cada perfil.
- El análisis por clase confirma que seis clases escasas de full23 obtuvieron F1 cero;
  las matrices actuales son heatmaps de conteos absolutos, no matrices normalizadas.
- Los nueve entrenamientos sumaron 2:01:11 de A100 y ~11.86 CPU-h; consumo y estabilidad
  están documentados en `docs/results.md` con las limitaciones de muestreo GPU.
