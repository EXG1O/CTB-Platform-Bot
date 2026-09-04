from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment

import service

from ...flags import auth_not_required
from ...models import InvoicePayload, User
from .data import (
    PAYMENT_FAILED_TEXT,
    PAYMENT_SUCCESS_TEXT,
    PAYMENT_SUPPORT_COMMAND,
    PAYMENT_SUPPORT_TEXT,
    PRE_PAYMENT_FAILED_SHORT_TEXT,
)

import logging

logger = logging.getLogger(__name__)

router = Router(name='Payment')


@router.pre_checkout_query()
async def pre_checkout_query_handler(
    pre_checkout_query: PreCheckoutQuery, user: User, service_client: service.Client
) -> None:
    try:
        payload: InvoicePayload = InvoicePayload.model_validate_json(
            pre_checkout_query.invoice_payload, by_alias=True
        )
        invoice: service.Invoice = await service_client.get_invoice(
            id=payload.id, user_id=user.service.id, type=service.InvoiceType.PREMIUM
        )

        if invoice.status == service.InvoiceStatus.PENDING:
            await pre_checkout_query.answer(ok=True)
            return
    except Exception:
        logger.exception(
            'Failed to process pre-checkout query for user (user_id=%d, payload=%s).',
            user.service.id,
            pre_checkout_query.invoice_payload,
        )

    await pre_checkout_query.answer(
        ok=False, error_message=PRE_PAYMENT_FAILED_SHORT_TEXT
    )


@router.message(F.successful_payment)
async def success_payment_handler(
    message: Message, user: User, service_client: service.Client
) -> None:
    payment: SuccessfulPayment | None = message.successful_payment
    assert payment

    try:
        payload: InvoicePayload = InvoicePayload.model_validate_json(
            payment.invoice_payload, by_alias=True
        )
        invoice: service.Invoice = await service_client.update_invoice_status(
            id=payload.id,
            user_id=user.service.id,
            type=service.InvoiceType.PREMIUM,
            status=service.InvoiceStatus.PAID,
            telegram_charge_id=payment.telegram_payment_charge_id,
        )
    except Exception:
        logger.exception(
            'Failed to process successful payment for user (user_id=%d, payload=%s).',
            user.service.id,
            payment.invoice_payload,
        )
        await message.answer(PAYMENT_FAILED_TEXT, parse_mode=ParseMode.HTML)
        raise
    else:
        await message.answer(
            PAYMENT_SUCCESS_TEXT.format(
                period_days=invoice.period_months * 30,
                amount_stars=invoice.amount_stars,
            ),
            parse_mode=ParseMode.HTML,
        )


@router.message(Command(PAYMENT_SUPPORT_COMMAND))
@auth_not_required
async def payment_support_command_handler(message: Message) -> None:
    await message.answer(PAYMENT_SUPPORT_TEXT, parse_mode=ParseMode.HTML)
