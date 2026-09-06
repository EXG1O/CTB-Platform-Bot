from fastapi import APIRouter, BackgroundTasks, Depends, Request, status

import aiogram

import bot
import core.payments

from .deps import verify_app_token, verify_telegram_token
from .models import DefaultKeyboard, InlineKeyboard, LinkPreviewOptions
from .schemas import (
    InitCheckoutRequest,
    InitCheckoutResponse,
    RefundPaymentRequest,
    SendTelegramMessageRequest,
)

from typing import TYPE_CHECKING
import asyncio
import logging

logger = logging.getLogger(__name__)

telegram_router = APIRouter(
    prefix='/telegram', dependencies=[Depends(verify_telegram_token)]
)
app_router = APIRouter(dependencies=[Depends(verify_app_token)])


@telegram_router.post('/webhook/', status_code=status.HTTP_202_ACCEPTED)
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks) -> None:
    background_tasks.add_task(bot.feed_update, await request.body())


@app_router.post('/init-checkout/', status_code=status.HTTP_201_CREATED)
async def init_checkout(data: InitCheckoutRequest) -> InitCheckoutResponse:
    url: str = await core.payments.get_checkout_url(
        user_service_id=data.user_service_id,
        title=data.title,
        description=data.description,
        period_months=data.period_months,
        amount=data.amount,
    )
    return InitCheckoutResponse(url=url)


async def _refund_payments(data: list[RefundPaymentRequest]) -> None:
    results: list[BaseException | None] = await asyncio.gather(
        *[
            bot.limiter.throttle_external_call(
                core.payments.refund_payment(
                    user_service_id=item.user_service_id,
                    user_telegram_id=item.user_telegram_id,
                    invoice_id=item.invoice_id,
                    telegram_charge_id=item.telegram_charge_id,
                )
            )
            for item in data
        ],
        return_exceptions=True,
    )

    for result, item in zip(results, data, strict=True):
        if isinstance(result, BaseException):
            logger.error(
                'Failed to refund payment (user_service_id=%d, invoice_id=%d).',
                item.user_service_id,
                item.invoice_id,
                exc_info=result,
            )


@app_router.post('/refund-payments/', status_code=status.HTTP_202_ACCEPTED)
async def refund_payments(
    data: list[RefundPaymentRequest], background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(_refund_payments, data)


async def _send_telegram_message(data: SendTelegramMessageRequest) -> None:
    raw_options: LinkPreviewOptions = data.link_preview_options
    link_preview_options = aiogram.types.LinkPreviewOptions(
        is_disabled=raw_options.is_disabled,
        url=raw_options.url,
        prefer_small_media=raw_options.prefer_small_media,
        prefer_large_media=raw_options.prefer_large_media,
        show_above_text=raw_options.show_above_text,
    )
    keyboard: (
        aiogram.types.ReplyKeyboardMarkup | aiogram.types.InlineKeyboardMarkup | None
    ) = None

    if TYPE_CHECKING:
        raw_keyboard: DefaultKeyboard | InlineKeyboard | None

    if raw_keyboard := data.default_keyboard:
        keyboard = aiogram.types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    aiogram.types.KeyboardButton(text=button.text, style=button.style)
                    for button in row
                ]
                for row in raw_keyboard.rows
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
    elif raw_keyboard := data.inline_keyboard:
        keyboard = aiogram.types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    aiogram.types.InlineKeyboardButton(
                        text=button.text, url=button.url, style=button.style
                    )
                    for button in row
                ]
                for row in raw_keyboard.rows
            ]
        )

    results: list[BaseException | aiogram.types.Message] = await asyncio.gather(
        *[
            bot.limiter.throttle_external_call(
                bot.bot.send_message(
                    chat_id=chat_id,
                    text=data.text,
                    parse_mode=data.text_type,
                    link_preview_options=link_preview_options,
                    reply_markup=keyboard,
                    disable_notification=data.disable_notification,
                    protect_content=data.protect_content,
                )
            )
            for chat_id in data.chat_ids
        ],
        return_exceptions=True,
    )

    for result, chat_id in zip(results, data.chat_ids, strict=True):
        if isinstance(result, BaseException):
            logger.error(
                'Failed to send Telegram message to chat (chat_id=%d).',
                chat_id,
                exc_info=result,
            )


@app_router.post('/send-telegram-message/', status_code=status.HTTP_202_ACCEPTED)
async def send_telegram_message(
    data: SendTelegramMessageRequest, background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(_send_telegram_message, data)


async def _send_telegram_messages(data: list[SendTelegramMessageRequest]) -> None:
    results: list[BaseException | None] = await asyncio.gather(
        *[_send_telegram_message(item) for item in data], return_exceptions=True
    )

    for result, item in zip(results, data, strict=True):
        if isinstance(result, BaseException):
            logger.error(
                'Failed to send Telegram message to chats (chat_ids=%s).',
                item.chat_ids,
                exc_info=result,
            )


@app_router.post('/send-telegram-messages/', status_code=status.HTTP_202_ACCEPTED)
async def send_telegram_messages(
    data: list[SendTelegramMessageRequest], background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(_send_telegram_messages, data)
