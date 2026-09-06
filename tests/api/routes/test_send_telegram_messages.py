from fastapi import status

import httpx

from api.enums import TextType
from api.models import DefaultKeyboard, DefaultKeyboardButton
from api.schemas import SendTelegramMessageRequest
from core.settings import APP_TOKEN

from ..base import APITestCase

from itertools import chain
from unittest.mock import AsyncMock


class SendTelegramMessagesTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_bot_send_message: AsyncMock = self.mock_bot.send_message

    def test_send_multiple_messages(self) -> None:
        request_data: list[SendTelegramMessageRequest] = [
            SendTelegramMessageRequest(
                chat_ids=[1, 2, 3], text='Message 1.', text_type=TextType.HTML
            ),
            SendTelegramMessageRequest(
                chat_ids=[10, 11], text='Message 2.', text_type=TextType.MARKDOWN
            ),
            SendTelegramMessageRequest(chat_ids=[20], text='Message 3.'),
        ]

        response: httpx.Response = self.client.post(
            '/send-telegram-messages/',
            headers={'X-API-KEY': APP_TOKEN},
            json=[item.model_dump() for item in request_data],
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(
            self.mock_bot_send_message.await_count,
            sum(len(item.chat_ids) for item in request_data),
        )

        call_texts: list[str] = [
            call.kwargs['text'] for call in self.mock_bot_send_message.await_args_list
        ]
        self.assertEqual(
            call_texts.count(request_data[0].text), len(request_data[0].chat_ids)
        )
        self.assertEqual(
            call_texts.count(request_data[1].text), len(request_data[1].chat_ids)
        )
        self.assertEqual(
            call_texts.count(request_data[2].text), len(request_data[2].chat_ids)
        )

        called_chat_ids = [
            call.kwargs['chat_id']
            for call in self.mock_bot_send_message.await_args_list
        ]
        self.assertEqual(
            sorted(called_chat_ids),
            list(chain.from_iterable(item.chat_ids for item in request_data)),
        )

    def test_send_messages_different_configurations(self) -> None:
        request_data_keyboard: DefaultKeyboard = DefaultKeyboard(
            rows=[[DefaultKeyboardButton(text='OK')]]
        )
        request_data: list[SendTelegramMessageRequest] = [
            SendTelegramMessageRequest(
                chat_ids=[1, 2],
                text='Message with keyboard.',
                default_keyboard=request_data_keyboard,
                disable_notification=True,
            ),
            SendTelegramMessageRequest(
                chat_ids=[3],
                text='Protected message.',
                protect_content=True,
            ),
        ]

        response: httpx.Response = self.client.post(
            '/send-telegram-messages/',
            headers={'X-API-KEY': APP_TOKEN},
            json=[item.model_dump() for item in request_data],
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(self.mock_bot_send_message.await_count, 3)

        calls_list = self.mock_bot_send_message.await_args_list

        for index in range(2):
            self.assertEqual(calls_list[index].kwargs['text'], request_data[0].text)
            self.assertIsNotNone(calls_list[index].kwargs['reply_markup'])
            self.assertTrue(calls_list[index].kwargs['disable_notification'])

        self.assertEqual(calls_list[2].kwargs['text'], request_data[1].text)
        self.assertIsNone(calls_list[2].kwargs.get('reply_markup'))
        self.assertTrue(calls_list[2].kwargs['protect_content'])
