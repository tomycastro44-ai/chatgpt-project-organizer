from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.system import DemoSummaryResponse
from app.services.demo_dataset import DemoDatasetError, DemoDatasetService

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/summary", response_model=DemoSummaryResponse)
def demo_summary(settings: Settings = Depends(get_settings)) -> DemoSummaryResponse:
    try:
        summary = DemoDatasetService(settings.demo_data_dir).summary()
    except DemoDatasetError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return DemoSummaryResponse(**summary.__dict__)
