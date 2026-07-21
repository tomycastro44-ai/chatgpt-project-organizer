from fastapi import APIRouter, HTTPException, Query, Request, status

from app.schemas.analysis import (
    AnalysisCreateRequest,
    AnalysisRunDetailResponse,
    AnalysisRunSummaryResponse,
    FindingListResponse,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis-runs", tags=["analysis"])


def service_for(request: Request) -> AnalysisService:
    return AnalysisService(request.app.state.database_engine)


@router.post("", response_model=AnalysisRunDetailResponse, status_code=status.HTTP_201_CREATED)
def create_analysis(payload: AnalysisCreateRequest, request: Request) -> AnalysisRunDetailResponse:
    try:
        result = service_for(request).run(payload.batch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import batch not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AnalysisRunDetailResponse.model_validate(result)


@router.get("", response_model=list[AnalysisRunSummaryResponse])
def list_analyses(
    request: Request,
    batch_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[AnalysisRunSummaryResponse]:
    return [AnalysisRunSummaryResponse.model_validate(item) for item in service_for(request).list_runs(batch_id, limit)]


@router.get("/{run_id}", response_model=AnalysisRunDetailResponse)
def get_analysis(run_id: str, request: Request) -> AnalysisRunDetailResponse:
    try:
        result = service_for(request).get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analysis run not found") from exc
    return AnalysisRunDetailResponse.model_validate(result)


@router.get("/{run_id}/findings", response_model=FindingListResponse)
def list_findings(
    run_id: str,
    request: Request,
    finding_type: str | None = Query(default=None),
    confidence: str | None = Query(default=None, pattern="^(ALTA|MEDIA|BAJA)$"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> FindingListResponse:
    try:
        items, total = service_for(request).list_findings(run_id, finding_type, confidence, limit, offset)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Analysis run not found") from exc
    return FindingListResponse(items=items, total=total, limit=limit, offset=offset)
