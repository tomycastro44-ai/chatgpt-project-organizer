# O.T. 010 — Informe de validación

Fecha: 2026-07-20  
Versión: `OT010-v1`  
Estado: `EN_REVISION`

## Resultado

```text
OT-010 VALIDATION: OK
Backend tests: 31
Repository contracts: 7
Frontend tests: 3
Acceptance cases: 32
Canonical analysis: 33 chats / 45 findings / 61 evidences
Approved sources unchanged: 3
Frontend production build: OK
```

## Validaciones funcionales

- importación del dataset aprobado: 33 chats y 51 mensajes;
- creación de `AnalysisRun` completada;
- 45 findings persistidos;
- 61 evidencias persistidas;
- duplicado exacto `CHAT-004 → CHAT-003`;
- duplicado parcial `CHAT-005 ↔ CHAT-006`, sin fusión;
- nueve versiones resueltas;
- V8 actual y V9/V9.1 descartadas aun apareciendo en el mismo mensaje;
- V11 descartada mediante referencia posterior “esta versión”;
- contradicción `CHAT-032/CHAT-033` resuelta como `ACTIVO` por evidencia explícita más reciente;
- filtros de findings por tipo y confianza;
- ejecuciones repetidas con las mismas `stable_key`;
- fuentes aprobadas sin cambios SHA-256.

## Validaciones técnicas

- instalación desde fuente limpia: `OK`;
- instalación Python en entorno virtual aislado: `OK`;
- `pip check` en entorno aislado: `No broken requirements found`;
- instalación npm mediante `npm ci`: `OK`;
- vulnerabilidades npm de producción: `0`;
- frontend y backend arrancados conjuntamente: `OK`;
- proxy y endpoints reales: `OK`;
- compilación Vite de producción: `OK`;
- claves foráneas SQLite: `ON`;
- originales modificados por el análisis: `0`.

## Corrección localizada aplicada

El importador CSV podía conservar `updated_at = null` si el último mensaje no tenía timestamp, aunque existiera una fecha válida anterior. Se sustituyó por el último timestamp no nulo o, en su defecto, `created_at`.

La corrección:

- no modifica archivos fuente;
- no cambia el contrato de importación;
- es retrocompatible;
- permite ordenar correctamente evidencias posteriores.

## Límites verificados

No existen:

- llamadas a OpenAI;
- agrupación semántica de proyectos;
- propuestas aplicables;
- modificación de chats;
- aplicación de operaciones;
- Deshacer.
