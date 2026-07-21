from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.schemas.semantic import (
    SemanticCapabilityResponse,
    SemanticRunRequest,
    SemanticRunResponse,
    SemanticRunSummaryResponse,
)
from app.services.semantic_service import SemanticService

router = APIRouter(prefix="/semantic-runs", tags=["semantic-analysis"])


def service(request: Request) -> SemanticService:
    return SemanticService(request.app.state.database_engine, get_settings())


@router.get("/capabilities", response_model=SemanticCapabilityResponse)
def capabilities(request: Request) -> SemanticCapabilityResponse:
    return service(request).capabilities()


@router.post("", response_model=SemanticRunResponse, status_code=status.HTTP_201_CREATED)
def create_semantic_run(payload: SemanticRunRequest, request: Request) -> SemanticRunResponse:
    try:
        return service(request).run(payload.analysis_run_id, payload.mode)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Deterministic analysis run not found") from exc
    except ValueError as exc:
        code = 409 if "OPENAI_API_KEY" in str(exc) else 422
        raise HTTPException(status_code=code, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("", response_model=list[SemanticRunSummaryResponse])
def list_semantic_runs(request: Request) -> list[SemanticRunSummaryResponse]:
    return service(request).list_runs()


@router.get("/{run_id}", response_model=SemanticRunResponse)
def get_semantic_run(run_id: str, request: Request) -> SemanticRunResponse:
    try:
        return service(request).get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Semantic run not found") from exc
