from aiogram.methods import AnswerPreCheckoutQuery

import httpx

from bot.models import InvoicePayload
import service

from ...base import SERVICE_INVOICE_ID, SERVICE_USER_ID, BotTestCase

from http import HTTPStatus
from typing import Final
from unittest.mock import AsyncMock

INVOICE_PAYLOAD: Final[str] = InvoicePayload(id=SERVICE_INVOICE_ID).model_dump_json()


def build_service_invoice(status: service.InvoiceStatus) -> service.Invoice:
    return service.Invoice(
        id=SERVICE_INVOICE_ID,
        status=status,
        period_months=1,
        amount_stars=100,
        telegram_charge_id=None,
    )


class PreCheckoutQueryHandlerTestCase(BotTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_get_invoice: AsyncMock = self.mock_service_client.get_invoice

    def test_reject_not_pending(self) -> None:
        for status in (service.InvoiceStatus.PAID, service.InvoiceStatus.FAILED):
            with self.subTest(status=status):
                self.mock_get_invoice.return_value = build_service_invoice(status)
                self.feed_pre_checkout_query(INVOICE_PAYLOAD)

                answer: AnswerPreCheckoutQuery = self.get_requests(
                    AnswerPreCheckoutQuery
                )[-1]
                self.assertFalse(answer.ok)

    def test_reject_invalid_payload(self) -> None:
        self.feed_pre_checkout_query('invalid_json')

        self.mock_get_invoice.assert_not_awaited()

        answer: AnswerPreCheckoutQuery = self.get_requests(AnswerPreCheckoutQuery)[0]
        self.assertFalse(answer.ok)

    def test_reject_on_service_error(self) -> None:
        request = httpx.Request('GET', 'https://example.com/')
        self.mock_get_invoice.side_effect = httpx.HTTPStatusError(
            'Service unavailable',
            request=request,
            response=httpx.Response(HTTPStatus.SERVICE_UNAVAILABLE, request=request),
        )
        self.feed_pre_checkout_query(INVOICE_PAYLOAD)

        answer: AnswerPreCheckoutQuery = self.get_requests(AnswerPreCheckoutQuery)[0]
        self.assertFalse(answer.ok)

    def test_approve_pending_invoice(self) -> None:
        self.mock_get_invoice.return_value = build_service_invoice(
            service.InvoiceStatus.PENDING
        )
        self.feed_pre_checkout_query(INVOICE_PAYLOAD)

        self.mock_get_invoice.assert_awaited_once_with(
            id=SERVICE_INVOICE_ID,
            user_id=SERVICE_USER_ID,
            type=service.InvoiceType.PREMIUM,
        )

        requests: list[AnswerPreCheckoutQuery] = self.get_requests(
            AnswerPreCheckoutQuery
        )
        self.assertEqual(len(requests), 1)

        answer: AnswerPreCheckoutQuery = requests[0]
        self.assertTrue(answer.ok)
