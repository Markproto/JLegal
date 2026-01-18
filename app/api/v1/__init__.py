"""API v1 module."""
from fastapi import APIRouter
from app.api.v1.documents import router as documents_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
