# O.T. 009 — Importación funcional y normalización

## Objetivo

Implementar el primer recorrido funcional completo sobre OT008-v1: selección o carga de fuentes JSON/CSV/TXT, copia inmutable, normalización, persistencia SQLite y presentación del resultado.

## Implementación

- `ImportBatch`, `SourceFile`, `Chat`, `Message` e `ImportIssue`.
- Adaptadores deterministas para JSON, CSV y TXT.
- SHA-256 y almacenamiento protegido de originales.
- Errores aislados por archivo, registro o mensaje.
- API de importación, historial, detalle y chats normalizados.
- Interfaz React responsive para importación local y dataset aprobado.

## API

- `POST /api/v1/imports`
- `POST /api/v1/imports/demo`
- `GET /api/v1/imports`
- `GET /api/v1/imports/{batch_id}`
- `GET /api/v1/imports/{batch_id}/chats`

## Límites

No incluye GPT-5.6, análisis semántico, agrupación de proyectos, propuestas, aplicación, auditoría ni Deshacer.
