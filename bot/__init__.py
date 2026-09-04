from aiogram import Bot, Dispatcher
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.enums import UpdateType
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import LabeledPrice, Update

from core.settings import APP_URL, BOT_TOKEN, REDIS_URL, TELEGRAM_TOKEN
import service

from .handlers import router
from .middlewares import UserMiddleware, UserTermsCheckMiddleware
from .models import InvoicePayload
from .session import Session

from collections.abc import Awaitable
from typing import Any, Final
import logging

logger = logging.getLogger(__name__)

_ALLOWED_UPDATES: Final[tuple[UpdateType, ...]] = (
    UpdateType.MESSAGE,
    UpdateType.PRE_CHECKOUT_QUERY,
)

bot = Bot(token=BOT_TOKEN, session=Session())
service_client = service.Client()

dispatcher = Dispatcher(
    service_client=service_client, storage=RedisStorage.from_url(REDIS_URL)
)

for event_type in _ALLOWED_UPDATES:
    observer: TelegramEventObserver = dispatcher.observers[event_type]
    observer.middleware(UserMiddleware())
    observer.middleware(UserTermsCheckMiddleware())

dispatcher.include_router(router)


async def feed_update(data: Any) -> None:
    update: Update | None = None
    update_context: dict[str, Any] = {'bot': bot}

    if isinstance(data, str | bytes | bytearray):
        update = Update.model_validate_json(data, context=update_context)
    else:
        update = Update.model_validate(data, context=update_context)

    await dispatcher.feed_update(bot, update)


async def create_invoice_link(
    title: str, description: str, amount: int, payload: InvoicePayload
) -> str:
    return await bot.create_invoice_link(
        title=title,
        description=description,
        currency='XTR',
        prices=[LabeledPrice(label=title, amount=amount)],
        payload=payload.model_dump_json(by_alias=True),
    )


async def start() -> None:
    await bot.set_webhook(
        str(APP_URL / 'telegram' / 'webhook/'),
        allowed_updates=list(_ALLOWED_UPDATES),
        secret_token=TELEGRAM_TOKEN,
    )


async def _safe_call(coro: Awaitable[Any]) -> None:
    try:
        await coro
    except Exception:
        logger.exception('Error during shutdown.')


async def stop() -> None:
    await _safe_call(bot.delete_webhook())
    await _safe_call(bot.session.close())
    await _safe_call(service_client.close())


__all__ = [
    'InvoicePayload',
    'bot',
    'service_client',
    'dispatcher',
    'feed_update',
    'create_invoice_link',
    'start',
    'stop',
]
