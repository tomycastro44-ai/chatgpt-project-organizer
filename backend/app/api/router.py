from fastapi import APIRouter

from app.api.routes import analysis, demo, health, imports, proposals, semantic, system

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(demo.router)
api_router.include_router(imports.router)
api_router.include_router(analysis.router)
api_router.include_router(semantic.router)

api_router.include_router(proposals.router)
