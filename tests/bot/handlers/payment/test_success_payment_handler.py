from aiogram.methods import SendMessage, SendPhoto
from aiogram.types import SuccessfulPayment

import httpx

from bot.handlers.payment.data import PAYMENT_FAILED_TEXT, PAYMENT_SUCCESS_TEXT
import service

from ...base import SERVICE_INVOICE_ID, SERVICE_USER_ID, BotTestCase
from .test_pre_checkout_query_handler import INVOICE_PAYLOAD

from http import HTTPStatus
from typing import Final
from unittest.mock import AsyncMock

TELEGRAM_PAYMENT_CHARGE_ID: Final[str] = 'charge-123456789'
SUCCESSFUL_PAYMENT: Final[SuccessfulPayment] = SuccessfulPayment(
    currency='XTR',
    total_amount=100,
    invoice_payload=INVOICE_PAYLOAD,
    telegram_payment_charge_id=TELEGRAM_PAYMENT_CHARGE_ID,
    provider_payment_charge_id='telegram',
)


class SuccessPaymentHandlerTestCase(BotTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_update_invoice_status: AsyncMock = (
            self.mock_service_client.update_invoice_status
        )

    def test_send_failed_message(self) -> None:
        request = httpx.Request('GET', 'https://example.com/')
        self.mock_update_invoice_status.side_effect = httpx.HTTPStatusError(
            'Service unavailable',
            request=request,
            response=httpx.Response(HTTPStatus.SERVICE_UNAVAILABLE, request=request),
        )

        with self.assertRaises(httpx.HTTPStatusError):
            self.feed_message(successful_payment=SUCCESSFUL_PAYMENT)

        requests: list[SendMessage] = self.get_requests(SendMessage)
        self.assertEqual(len(requests), 1)

        message: SendMessage = requests[0]
        self.assertEqual(message.text, PAYMENT_FAILED_TEXT)
        self.assertEqual(self.get_requests(SendPhoto), [])

    def test_mark_invoice_paid(self) -> None:
        self.feed_message(successful_payment=SUCCESSFUL_PAYMENT)

        self.mock_update_invoice_status.assert_awaited_once_with(
            id=SERVICE_INVOICE_ID,
            user_id=SERVICE_USER_ID,
            type=service.InvoiceType.PREMIUM,
            status=service.InvoiceStatus.PAID,
            telegram_charge_id=TELEGRAM_PAYMENT_CHARGE_ID,
        )

        requests: list[SendPhoto] = self.get_requests(SendPhoto)
        self.assertEqual(len(requests), 1)

        photo: SendPhoto = requests[0]
        self.assertEqual(photo.caption, PAYMENT_SUCCESS_TEXT)
