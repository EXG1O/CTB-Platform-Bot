from fastapi import status

import aiogram

import httpx

from core.settings import TELEGRAM_TOKEN

from ..base import APITestCase

from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock, patch


class TelegramWebhookTestCase(APITestCase):
    def test_valid_telegram_update(self) -> None:
        request_data = aiogram.types.Update(
            update_id=1,
            message=aiogram.types.Message(
                message_id=1,
                chat=aiogram.types.Chat(id=1, type=aiogram.enums.ChatType.PRIVATE),
                text='/start',
                date=datetime.now(UTC),
            ),
        )

        with patch(
            'bot.dispatcher.feed_update', new_callable=AsyncMock
        ) as mock_feed_update:
            response: httpx.Response = self.client.post(
                '/telegram/webhook/',
                headers={'X-Telegram-Bot-Api-Secret-Token': TELEGRAM_TOKEN},
                json=request_data.model_dump(),
            )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_feed_update.assert_awaited_once()
        self.assertEqual(
            cast(aiogram.types.Update, mock_feed_update.call_args.args[1]).model_dump(),
            request_data.model_dump(),
        )
