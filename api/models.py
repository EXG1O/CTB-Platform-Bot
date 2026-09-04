from pydantic import BaseModel

from .enums import KeyboardButtonStyle


class LinkPreviewOptions(BaseModel):
    is_disabled: bool
    url: str | None = None
    prefer_small_media: bool | None = None
    prefer_large_media: bool | None = None
    show_above_text: bool = False


class KeyboardButton(BaseModel):
    text: str
    style: KeyboardButtonStyle = KeyboardButtonStyle.DEFAULT


class Keyboard[T: KeyboardButton](BaseModel):
    rows: list[list[T]]


class DefaultKeyboardButton(KeyboardButton):
    pass


class DefaultKeyboard(Keyboard[DefaultKeyboardButton]):
    pass


class InlineKeyboardButton(KeyboardButton):
    url: str | None = None


class InlineKeyboard(Keyboard[InlineKeyboardButton]):
    pass
