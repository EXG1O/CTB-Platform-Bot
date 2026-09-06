from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from ...flags import accepted_terms_not_required
from ...models import User
from .data import WELCOME_KEYBOARD, WELCOME_TEXT

router = Router(name='Home')


@router.message(CommandStart)
@accepted_terms_not_required
async def start_command_handler(message: Message, user: User) -> None:
    await message.reply(
        WELCOME_TEXT.format(user_full_name=user.telegram.full_name),
        parse_mode=ParseMode.HTML,
        reply_markup=WELCOME_KEYBOARD,
    )
