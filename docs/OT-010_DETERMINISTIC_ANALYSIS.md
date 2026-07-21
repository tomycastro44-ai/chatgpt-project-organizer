# O.T. 010 — Motor de análisis determinista y evidencias

## Estado

- Fase: **FASE 4 — Construcción**
- Estado del entregable: **EN_REVISION**
- Versión: **OT010-v1**
- Base: **OT009-v1 aprobada**

## Objetivo

Construir la capa reproducible que detecta hechos objetivos antes de integrar interpretación semántica con GPT-5.6.

## Implementación

### Persistencia

Nuevas tablas:

- `analysis_runs`;
- `analysis_findings`;
- `analysis_evidence`;
- `analysis_finding_evidence`.

No se altera ni elimina ninguna tabla de importación.

### Findings implementados

- `EXACT_DUPLICATE`;
- `PARTIAL_DUPLICATE`;
- `VERSION_STATUS`;
- `DECISION`;
- `TASK`;
- `STATE_SIGNAL`;
- `STATE_PRECEDENCE`.

### Evidencia

Cada finding conserva:

- chat afectado;
- chat relacionado cuando corresponde;
- mensaje;
- cita textual;
- fecha disponible;
- nivel de precedencia;
- confianza `ALTA`, `MEDIA` o `BAJA`.

### Reglas críticas

1. Los duplicados exactos se detectan mediante fingerprint normalizado.
2. Los duplicados parciales requieren solapamiento léxico fuerte y nunca se fusionan automáticamente.
3. Las versiones se resuelven mediante la evidencia explícita más reciente.
4. Las decisiones que usan “esta versión” heredan la última referencia de versión del mismo chat.
5. Cuando varias versiones aparecen en un mensaje, cada versión se evalúa en su propia cláusula.
6. Las contradicciones de estado conservan ambas evidencias y prevalece la decisión explícita más reciente.

## Resultado canónico

Sobre el dataset O.T. 006:

- 33 chats analizados;
- 45 findings;
- 61 evidencias persistidas;
- 1 duplicado exacto;
- 1 duplicado parcial;
- 9 versiones resueltas;
- 16 señales de decisión;
- 11 señales de tarea;
- 7 findings de estado, incluida la precedencia ACTIVO sobre CERRADO.

## API

```text
POST /api/v1/analysis-runs
GET  /api/v1/analysis-runs
GET  /api/v1/analysis-runs/{run_id}
GET  /api/v1/analysis-runs/{run_id}/findings
```

## Interfaz

La pantalla Analysis permite:

- analizar el último lote;
- importar el dataset demo si no existe lote;
- consultar métricas;
- revisar findings agrupados;
- desplegar las citas que justifican cada resultado;
- volver a la importación sin perder la base aprobada.

## Corrección localizada incluida

El normalizador CSV podía dejar `updated_at` vacío cuando el último mensaje carecía de timestamp. Se corrigió para utilizar el último timestamp no nulo o la fecha de creación. No cambia el formato ni los datos fuente.

## Fuera de alcance

- GPT-5.6;
- agrupación semántica de proyectos;
- memoria operativa final;
- propuestas;
- revisión humana persistida;
- aplicación de operaciones;
- auditoría de aplicación;
- Deshacer.
