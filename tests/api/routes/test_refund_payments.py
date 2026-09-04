from fastapi import status

import httpx

from api.schemas import RefundPaymentRequest
from core.settings import APP_TOKEN
from service import InvoiceStatus, InvoiceType

from ..base import APITestCase

from unittest.mock import AsyncMock


class RefundPaymentsTestCase(APITestCase):
    def test_refund_payment(self) -> None:
        request_date_item: RefundPaymentRequest = RefundPaymentRequest(
            user_service_id=1,
            user_telegram_id=1,
            invoice_id=1,
            telegram_charge_id='charge_123456789',
        )

        mock_bot_refund_star_payment: AsyncMock = self.mock_bot.refund_star_payment
        mock_service_client_update_invoice_status: AsyncMock = (
            self.mock_service_client.update_invoice_status
        )

        response: httpx.Response = self.client.post(
            '/refund-payments/',
            headers={'X-API-KEY': APP_TOKEN},
            json=[request_date_item.model_dump()],
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_bot_refund_star_payment.assert_awaited_once_with(
            user_id=request_date_item.user_telegram_id,
            telegram_payment_charge_id=request_date_item.telegram_charge_id,
        )
        mock_service_client_update_invoice_status.assert_awaited_once_with(
            id=request_date_item.invoice_id,
            user_id=request_date_item.user_service_id,
            type=InvoiceType.PREMIUM,
            status=InvoiceStatus.REFUNDED,
        )
