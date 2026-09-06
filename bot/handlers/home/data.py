from aiogram.enums import ButtonStyle
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from typing import Final

WELCOME_TEXT: Final[str] = """\
✨ <b>Welcome, {user_full_name}!</b>

⚡️ A user-friendly platform that lets you easily create your own multifunctional Telegram bot with no coding required.
"""
WELCOME_KEYBOARD: Final[InlineKeyboardMarkup] = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Constructor Telegram Bots',
                url='https://constructor.exg1o.org/',
                style=ButtonStyle.PRIMARY,
            )
        ]
    ]
)
