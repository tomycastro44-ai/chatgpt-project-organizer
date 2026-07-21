from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status

from app.core.config import Settings, get_settings
from app.schemas.imports import ChatListResponse, ImportBatchDetailResponse, ImportBatchSummaryResponse
from app.services.import_service import ImportInput, ImportService

router = APIRouter(prefix="/imports", tags=["imports"])


def service_for(request: Request) -> ImportService:
    settings = get_settings()
    return ImportService(
        request.app.state.database_engine,
        settings.imports_dir,
        settings.max_import_file_bytes,
        settings.max_import_files,
    )


@router.post("", response_model=ImportBatchDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_import(request: Request, files: list[UploadFile] = File(...)) -> ImportBatchDetailResponse:
    settings = get_settings()
    if len(files) > settings.max_import_files:
        raise HTTPException(status_code=413, detail=f"Maximum files per batch: {settings.max_import_files}")
    inputs: list[ImportInput] = []
    for upload in files:
        upload.file.seek(0, 2)
        size_bytes = upload.file.tell()
        upload.file.seek(0)
        if size_bytes > settings.max_import_file_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"{upload.filename or 'source.bin'} exceeds {settings.max_import_file_bytes} bytes",
            )
        content = await upload.read()
        inputs.append(ImportInput(upload.filename or "source.bin", content, upload.content_type or "application/octet-stream"))
    try:
        batch = service_for(request).import_inputs(inputs, "upload")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ImportBatchDetailResponse.model_validate(batch)


@router.post("/demo", response_model=ImportBatchDetailResponse, status_code=status.HTTP_201_CREATED)
def import_demo_sources(request: Request) -> ImportBatchDetailResponse:
    settings = get_settings()
    inputs = [
        ImportInput(path.name, path.read_bytes(), _mime_for(path))
        for path in sorted(settings.demo_source_dir.iterdir())
        if path.is_file() and path.suffix.lower() in {".json", ".csv", ".txt"}
    ]
    batch = service_for(request).import_inputs(inputs, "approved_demo")
    return ImportBatchDetailResponse.model_validate(batch)


@router.get("", response_model=list[ImportBatchSummaryResponse])
def list_imports(request: Request, limit: int = Query(20, ge=1, le=100)) -> list[ImportBatchSummaryResponse]:
    return [ImportBatchSummaryResponse.model_validate(item) for item in service_for(request).list_batches(limit)]


@router.get("/{batch_id}", response_model=ImportBatchDetailResponse)
def get_import(batch_id: str, request: Request) -> ImportBatchDetailResponse:
    try:
        batch = service_for(request).get_batch(batch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import batch not found") from exc
    return ImportBatchDetailResponse.model_validate(batch)


@router.get("/{batch_id}/chats", response_model=ChatListResponse)
def list_imported_chats(
    batch_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ChatListResponse:
    try:
        service_for(request).get_batch(batch_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Import batch not found") from exc
    chats = service_for(request).list_chats(batch_id, limit=limit, offset=offset)
    return ChatListResponse(items=chats, limit=limit, offset=offset)


def _mime_for(path: Path) -> str:
    return {
        ".json": "application/json",
        ".csv": "text/csv",
        ".txt": "text/plain",
    }.get(path.suffix.lower(), "application/octet-stream")
