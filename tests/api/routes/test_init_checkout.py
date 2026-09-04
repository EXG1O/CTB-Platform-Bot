from fastapi import status

import aiogram.exceptions

import httpx

from api.schemas import InitCheckoutRequest
from core.settings import APP_TOKEN
import service

from ..base import APITestCase

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock, Mock


class InitCheckoutTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.request_data = InitCheckoutRequest(
            user_service_id=1,
            title='Premium',
            description='Test description',
            period_months=1,
            amount=100,
        )

        self.mock_invoice = service.Invoice(
            id=1,
            status=service.InvoiceStatus.PENDING,
            period_months=self.request_data.period_months,
            amount_stars=self.request_data.amount,
            telegram_charge_id=None,
        )

        self.mock_service_client_create_invoice: AsyncMock = (
            self.mock_service_client.create_invoice
        )
        self.mock_bot_create_invoice_link: AsyncMock = self.mock_bot.create_invoice_link

    def test_init_checkout(self) -> None:
        mock_invoice_link: str = 'https://example.com/'

        mock_service_client_create_invoice: AsyncMock = (
            self.mock_service_client.create_invoice
        )
        mock_bot_create_invoice_link: AsyncMock = self.mock_bot.create_invoice_link

        mock_service_client_create_invoice.return_value = self.mock_invoice
        mock_bot_create_invoice_link.return_value = mock_invoice_link

        response: httpx.Response = self.client.post(
            '/init-checkout/',
            headers={'X-API-KEY': APP_TOKEN},
            json=self.request_data.model_dump(),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mock_service_client_create_invoice.assert_awaited_once_with(
            user_id=self.request_data.user_service_id,
            type=service.InvoiceType.PREMIUM,
            period_months=self.request_data.period_months,
            amount_stars=self.request_data.amount,
        )

        mock_bot_create_invoice_link.assert_awaited_once()
        bot_create_invoice_call_kwargs: Mapping[str, Any] = (
            mock_bot_create_invoice_link.call_args.kwargs
        )
        self.assertEqual(
            bot_create_invoice_call_kwargs['title'], self.request_data.title
        )
        self.assertEqual(
            bot_create_invoice_call_kwargs['description'], self.request_data.description
        )

        response_data: dict[str, Any] = response.json()
        self.assertEqual(response_data['url'], mock_invoice_link)

    def test_init_checkout_rollback_on_error(self) -> None:
        mock_service_client_create_invoice: AsyncMock = (
            self.mock_service_client.create_invoice
        )
        mock_service_client_update_invoice_status: AsyncMock = (
            self.mock_service_client.update_invoice_status
        )
        mock_bot_create_invoice_link: AsyncMock = self.mock_bot.create_invoice_link

        mock_service_client_create_invoice.return_value = self.mock_invoice
        mock_bot_create_invoice_link.side_effect = aiogram.exceptions.TelegramAPIError(
            Mock(), 'Bad Request'
        )

        with self.assertRaises(aiogram.exceptions.TelegramAPIError):
            self.client.post(
                '/init-checkout/',
                headers={'X-API-KEY': APP_TOKEN},
                json=self.request_data.model_dump(),
            )

        mock_service_client_update_invoice_status.assert_awaited_once_with(
            id=self.mock_invoice.id,
            user_id=self.request_data.user_service_id,
            type=service.InvoiceType.PREMIUM,
            status=service.InvoiceStatus.FAILED,
        )
