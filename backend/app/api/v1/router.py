from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, content_blocks, pages

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(pages.router, prefix="/pages", tags=["pages"])
api_router.include_router(
    content_blocks.router, prefix="/content-blocks", tags=["content-blocks"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
