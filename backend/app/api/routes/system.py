from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.system import SystemResponse

router = APIRouter(tags=["system"])


@router.get("/system", response_model=SystemResponse)
def system_information(settings: Settings = Depends(get_settings)) -> SystemResponse:
    database_kind = "sqlite" if settings.database_url.startswith("sqlite") else "configured"
    return SystemResponse(
        api_version="v1",
        database=database_kind,
        demo_mode=True,
        openai_configured=bool(settings.openai_api_key),
        originals_immutable=True,
    )
