# ADR-0004 — Motor determinista y evidencia persistida

## Estado

Aceptado para revisión en O.T. 010.

## Decisión

Separar el análisis objetivo y reproducible de la interpretación semántica futura.

El motor determinista:

- opera exclusivamente sobre chats normalizados;
- no llama a OpenAI ni a servicios externos;
- genera `AnalysisRun`, `AnalysisFinding` y `AnalysisEvidence`;
- usa claves estables para comparar ejecuciones;
- conserva citas, conversación, mensaje y precedencia;
- nunca modifica los archivos fuente ni aplica cambios organizativos.

## Motivo

Duplicados exactos, reglas de precedencia, referencias de versión y expresiones explícitas deben producir el mismo resultado en cada ejecución. GPT-5.6 se incorporará después para relaciones semánticas y reconstrucciones que no puedan resolverse de forma segura con reglas.

## Consecuencias

- resultados auditables y aptos para regresión;
- separación clara entre hechos detectados e inferencias futuras;
- la agrupación de proyectos y las propuestas siguen deshabilitadas;
- los casos ambiguos permanecen como findings de revisión, no como cambios automáticos.
