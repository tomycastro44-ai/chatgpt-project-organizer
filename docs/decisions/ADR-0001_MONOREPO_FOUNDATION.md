# ADR-0001 — Monorepo technical foundation

## Status

Accepted for O.T. 008 review.

## Decision

Use one repository containing `frontend`, `backend`, approved `demo-data`, documentation, tests, screenshots, and scripts.

## Reason

The MVP is evaluated as one product and requires synchronized contracts, reproducible setup, and a single valid continuation base.

## Consequences

- Frontend and backend changes remain traceable together.
- Shared demo fixtures are not duplicated.
- CI can validate the whole product from one checkout.
- Domain implementation must extend this repository rather than branch into parallel projects.
