from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.schemas.proposals import (
    AppliedOperationResponse,
    AuditEventResponse,
    PreviewResponse,
    ProposalReviewRequest,
    ProposalRunRequest,
    ProposalRunResponse,
    ProposalRunSummaryResponse,
    UndoOperationResponse,
)
from app.services.proposal_service import ProposalService

router = APIRouter(tags=["proposals-and-undo"])


def service(request: Request) -> ProposalService:
    return ProposalService(request.app.state.database_engine, get_settings())


@router.post("/proposal-runs", response_model=ProposalRunResponse, status_code=status.HTTP_201_CREATED)
def create_proposal_run(payload: ProposalRunRequest, request: Request) -> ProposalRunResponse:
    try:
        return service(request).create_run(payload.semantic_run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Semantic run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/proposal-runs", response_model=list[ProposalRunSummaryResponse])
def list_proposal_runs(request: Request) -> list[ProposalRunSummaryResponse]:
    return service(request).list_runs()


@router.get("/proposal-runs/{run_id}", response_model=ProposalRunResponse)
def get_proposal_run(run_id: str, request: Request) -> ProposalRunResponse:
    try:
        return service(request).get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal run not found") from exc


@router.post("/proposal-runs/{run_id}/approve-safe", response_model=ProposalRunResponse)
def approve_safe(run_id: str, request: Request) -> ProposalRunResponse:
    try:
        return service(request).approve_safe(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal run not found") from exc


@router.post("/proposal-runs/{run_id}/items/{item_id}/review", response_model=ProposalRunResponse)
def review_item(run_id: str, item_id: str, payload: ProposalReviewRequest, request: Request) -> ProposalRunResponse:
    try:
        return service(request).review_item(run_id, item_id, payload.decision, payload.correction, payload.note)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal run or item not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/proposal-runs/{run_id}/preview", response_model=PreviewResponse)
def preview(run_id: str, request: Request) -> PreviewResponse:
    try:
        return service(request).preview(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal run not found") from exc


@router.post("/proposal-runs/{run_id}/apply", response_model=AppliedOperationResponse, status_code=status.HTTP_201_CREATED)
def apply(run_id: str, request: Request) -> AppliedOperationResponse:
    try:
        return service(request).apply(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal run not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/applied-operations/{operation_id}/undo", response_model=UndoOperationResponse, status_code=status.HTTP_201_CREATED)
def undo(operation_id: str, request: Request) -> UndoOperationResponse:
    try:
        return service(request).undo(operation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applied operation not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/proposal-runs/{run_id}/audit", response_model=list[AuditEventResponse])
def audit(run_id: str, request: Request) -> list[AuditEventResponse]:
    try:
        return service(request).audit(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Proposal run not found") from exc
