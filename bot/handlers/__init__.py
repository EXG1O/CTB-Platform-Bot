from aiogram import Router

from . import home, payment

router = Router()
router.include_routers(home.router, payment.router)

__all__ = ['router']
