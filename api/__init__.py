from fastapi import APIRouter

from .routes import app_router, telegram_router

router = APIRouter()
router.include_router(telegram_router)
router.include_router(app_router)

__all__ = ['router']
