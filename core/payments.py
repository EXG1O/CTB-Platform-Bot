from aiogram.exceptions import TelegramAPIError

import bot
import service

from .exceptions import RefundPaymentError


async def get_checkout_url(
    user_service_id: int, title: str, description: str, period_months: int, amount: int
) -> str:
    invoice: service.Invoice = await bot.service_client.create_invoice(
        user_id=user_service_id,
        type=service.InvoiceType.PREMIUM,
        period_months=period_months,
        amount_stars=amount,
    )

    try:
        return await bot.create_invoice_link(
            title=title,
            description=description,
            amount=amount,
            payload=bot.InvoicePayload(id=invoice.id),
        )
    except TelegramAPIError:
        await bot.service_client.update_invoice_status(
            id=invoice.id,
            user_id=user_service_id,
            type=service.InvoiceType.PREMIUM,
            status=service.InvoiceStatus.FAILED,
        )
        raise


async def refund_payment(
    user_service_id: int,
    user_telegram_id: int,
    invoice_id: int,
    telegram_charge_id: str,
) -> None:
    result: bool = await bot.bot.refund_star_payment(
        user_id=user_telegram_id, telegram_payment_charge_id=telegram_charge_id
    )

    if not result:
        raise RefundPaymentError()

    await bot.service_client.update_invoice_status(
        id=invoice_id,
        user_id=user_service_id,
        type=service.InvoiceType.PREMIUM,
        status=service.InvoiceStatus.REFUNDED,
    )
