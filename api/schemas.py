from pydantic import BaseModel

from api.enums import TextType

from .models import DefaultKeyboard, InlineKeyboard, LinkPreviewOptions


class InitCheckoutRequest(BaseModel):
    user_service_id: int
    title: str
    description: str
    period_months: int
    amount: int


class InitCheckoutResponse(BaseModel):
    url: str


class RefundPaymentRequest(BaseModel):
    user_service_id: int
    user_telegram_id: int
    invoice_id: int
    telegram_charge_id: str


class SendTelegramMessageRequest(BaseModel):
    chat_ids: list[int]
    text: str
    text_type: TextType | None = None
    link_preview_options: LinkPreviewOptions = LinkPreviewOptions(is_disabled=True)
    default_keyboard: DefaultKeyboard | None = None
    inline_keyboard: InlineKeyboard | None = None
    disable_notification: bool = False
    protect_content: bool = False
