# O.T. 009 — Informe de validación

## Resultado

Estado: `OK`

## Pruebas superadas

- Backend y persistencia: **16 pruebas**.
- Contratos de repositorio: **4 pruebas**.
- Frontend React: **2 pruebas**.
- Total automatizado: **22 pruebas**.
- Matriz de aceptación O.T. 009: **30 casos**.

## Validación funcional

- JSON aprobado: **13 chats**.
- CSV aprobado: **9 chats**.
- TXT aprobado: **11 chats**.
- Total importado: **33 chats**.
- Mensajes normalizados: **51**.
- Archivos aceptados: **3 de 3**.
- Incidencias en dataset aprobado: **0**.
- Copias almacenadas con permisos de solo lectura: `0444` en la validación Linux.
- Originales de `demo-data/source`: hashes SHA-256 sin cambios.

## Validación de errores

- JSON inválido rechazado sin perder el archivo válido del mismo lote.
- Registro inválido aislado sin descartar conversaciones válidas.
- Formato no soportado conservado como fuente rechazada con incidencia estructurada.
- Importaciones repetidas conservan IDs externos y generan UUID internos independientes.

## Validación técnica

- Instalación limpia Python: `OK`.
- `pip check`: sin dependencias rotas.
- Instalación limpia npm mediante `npm ci`: `OK`.
- Pruebas Vitest: `OK`.
- Compilación TypeScript/Vite: `OK`.
- Vulnerabilidades npm de producción: `0`.
- Arranque real FastAPI: `OK`.
- Arranque real Vite: `OK`.
- Importación a través del proxy frontend → backend: `OK`.
- SQLite: 1 lote, 3 fuentes, 33 chats, 51 mensajes y 0 incidencias.
- Claves foráneas SQLite activadas.

## Entorno validado

- Python `3.13.5`.
- Node.js `22.16.0`.
- npm `10.9.2`.

## Límites confirmados

No se ha implementado GPT-5.6, análisis semántico, agrupación de proyectos, propuestas, aplicación, auditoría ni Deshacer.
