from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.flags import get_flag
from aiogram.enums import ButtonStyle, ParseMode
from aiogram.types import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    TelegramObject,
)

from ..flags import accepted_terms_not_required, auth_not_required
from ..models import User
from .types import MiddlewareData

from collections.abc import Awaitable, Callable
from typing import Any, Final, cast

TEXT: Final[str] = """\
To continue, you need to accept the <a href="https://constructor.exg1o.org/terms-of-service/">Terms of Service</a> by authorizing on the platform.
"""
LINK_PREVIEW_OPTIONS: Final[LinkPreviewOptions] = LinkPreviewOptions(is_disabled=True)
KEYBOARD: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Constructor Telegram Bots',
                url='https://constructor.exg1o.org/',
                style=ButtonStyle.SUCCESS,
            )
        ]
    ]
)


class UserTermsCheckMiddleware(BaseMiddleware):
    async def __call__(  # type: ignore [override]
        self,
        handler: Callable[[TelegramObject, MiddlewareData], Awaitable[Any]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> Any:
        if get_flag(
            cast(dict[str, Any], data), auth_not_required.flag.name
        ) or get_flag(
            cast(dict[str, Any], data), accepted_terms_not_required.flag.name
        ):
            return await handler(event, data)

        user: User = data['user']

        if user.service.accepted_terms:
            return await handler(event, data)

        bot: Bot = data['bot']
        chat: Chat = data['event_chat']

        await bot.send_message(
            chat_id=chat.id,
            text=TEXT,
            parse_mode=ParseMode.HTML,
            link_preview_options=LINK_PREVIEW_OPTIONS,
            reply_markup=KEYBOARD,
        )
        return None
