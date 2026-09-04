from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser

import service

from ..flags import auth_not_required
from ..models import User
from .types import MiddlewareData

from collections.abc import Awaitable, Callable
from typing import Any, cast


class UserMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore [override]
        self,
        handler: Callable[[TelegramObject, MiddlewareData], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        if get_flag(cast(dict[str, Any], data), auth_not_required.flag.name):
            return await handler(event, data)

        service_client: service.Client = data['service_client']
        telegram_user: TelegramUser = data['event_from_user']
        service_user: service.User = await service_client.create_user(
            telegram_id=telegram_user.id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
        )

        data['user'] = User(telegram=telegram_user, service=service_user)
        return await handler(event, data)
