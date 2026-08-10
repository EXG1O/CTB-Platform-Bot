from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Update

from core.settings import APP_URL, BOT_TOKEN, REDIS_URL, TELEGRAM_TOKEN
from service.client import ServiceClient

from .handlers import router
from .session import Session

from collections.abc import Awaitable
from typing import Any
import logging

logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, session=Session())
service = ServiceClient()

dispatcher = Dispatcher(service=service, storage=RedisStorage.from_url(REDIS_URL))
dispatcher.include_router(router)


async def feed_update(data: Any) -> None:
    update: Update | None = None
    update_context: dict[str, Any] = {'bot': bot}

    if isinstance(data, str | bytes | bytearray):
        update = Update.model_validate_json(data, context=update_context)
    else:
        update = Update.model_validate(data, context=update_context)

    await dispatcher.feed_update(bot, update)


async def start() -> None:
    await bot.set_webhook(
        str(APP_URL / 'telegram' / 'webhook/'),
        allowed_updates=[],
        secret_token=TELEGRAM_TOKEN,
    )


async def _safe_call(coro: Awaitable[Any]) -> None:
    try:
        await coro
    except Exception:
        logger.exception('Error during shutdown')


async def stop() -> None:
    await _safe_call(bot.delete_webhook())
    await _safe_call(bot.session.close())
    await _safe_call(service.close())


__all__ = ['bot', 'dispatcher', 'feed_update', 'start', 'stop']
