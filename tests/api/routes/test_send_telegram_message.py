from fastapi import status

import aiogram

import httpx

from api.enums import KeyboardButtonStyle, TextType
from api.models import (
    DefaultKeyboard,
    DefaultKeyboardButton,
    InlineKeyboard,
    InlineKeyboardButton,
    LinkPreviewOptions,
)
from api.schemas import SendTelegramMessageRequest
from core.settings import APP_TOKEN

from ..base import APITestCase

from collections.abc import Mapping
from typing import Any, cast
from unittest.mock import AsyncMock


class SendTelegramMessageTestCase(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.mock_bot_send_message: AsyncMock = self.mock_bot.send_message

    def test_send_simple_message(self) -> None:
        request_data: SendTelegramMessageRequest = SendTelegramMessageRequest(
            chat_ids=[1], text='Hello, World!'
        )

        response: httpx.Response = self.client.post(
            '/send-telegram-message/',
            headers={'X-API-KEY': APP_TOKEN},
            json=request_data.model_dump(),
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        call_kwargs: Mapping[str, Any] = self.mock_bot_send_message.call_args.kwargs
        self.assertEqual(call_kwargs['chat_id'], request_data.chat_ids[0])
        self.assertEqual(call_kwargs['text'], request_data.text)
        self.assertIsNone(call_kwargs['parse_mode'], TextType.HTML)
        self.assertEqual(
            cast(LinkPreviewOptions, call_kwargs['link_preview_options']).model_dump(),
            LinkPreviewOptions(is_disabled=True).model_dump(),
        )
        self.assertIsNone(call_kwargs['reply_markup'])
        self.assertFalse(call_kwargs['disable_notification'])
        self.assertFalse(call_kwargs['protect_content'])

    def test_send_message_with_default_keyboard(self) -> None:
        request_data_keyboard: DefaultKeyboard = DefaultKeyboard(
            rows=[
                [
                    DefaultKeyboardButton(text='Button 1'),
                    DefaultKeyboardButton(text='Button 2'),
                ],
                [DefaultKeyboardButton(text='Button 3')],
            ]
        )
        request_data: SendTelegramMessageRequest = SendTelegramMessageRequest(
            chat_ids=[1],
            text='Test default keyboard.',
            default_keyboard=request_data_keyboard,
            disable_notification=True,
        )

        response: httpx.Response = self.client.post(
            '/send-telegram-message/',
            headers={'X-API-KEY': APP_TOKEN},
            json=request_data.model_dump(),
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.mock_bot_send_message.assert_awaited_once()

        call_kwargs: Mapping[str, Any] = self.mock_bot_send_message.call_args.kwargs
        self.assertEqual(call_kwargs['chat_id'], request_data.chat_ids[0])
        self.assertEqual(call_kwargs['text'], request_data.text)
        self.assertTrue(call_kwargs['disable_notification'])

        reply_markup: aiogram.types.ReplyKeyboardMarkup = call_kwargs['reply_markup']
        self.assertTrue(isinstance(reply_markup, aiogram.types.ReplyKeyboardMarkup))
        self.assertEqual(len(reply_markup.keyboard), 2)
        self.assertEqual(len(reply_markup.keyboard[0]), 2)
        self.assertEqual(
            reply_markup.keyboard[0][0].text, request_data_keyboard.rows[0][0].text
        )
        self.assertEqual(
            reply_markup.keyboard[0][1].text, request_data_keyboard.rows[0][1].text
        )
        self.assertEqual(
            reply_markup.keyboard[1][0].text, request_data_keyboard.rows[1][0].text
        )

    def test_send_message_with_inline_keyboard(self) -> None:
        request_data_keyboard: InlineKeyboard = InlineKeyboard(
            rows=[
                [
                    InlineKeyboardButton(text='Button 1'),
                    InlineKeyboardButton(text='Link 2', url='https://example.com/'),
                ]
            ]
        )
        request_data: SendTelegramMessageRequest = SendTelegramMessageRequest(
            chat_ids=[1],
            text='Test inline keyboard.',
            inline_keyboard=request_data_keyboard,
            protect_content=True,
        )

        response: httpx.Response = self.client.post(
            '/send-telegram-message/',
            headers={'X-API-KEY': APP_TOKEN},
            json=request_data.model_dump(),
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.mock_bot_send_message.assert_awaited_once()

        call_kwargs: Mapping[str, Any] = self.mock_bot_send_message.call_args.kwargs
        self.assertEqual(call_kwargs['chat_id'], request_data.chat_ids[0])
        self.assertEqual(call_kwargs['text'], request_data.text)
        self.assertTrue(call_kwargs['protect_content'])

        reply_markup: aiogram.types.InlineKeyboardMarkup = call_kwargs['reply_markup']
        self.assertTrue(isinstance(reply_markup, aiogram.types.InlineKeyboardMarkup))
        self.assertEqual(len(reply_markup.inline_keyboard), 1)
        self.assertEqual(len(reply_markup.inline_keyboard[0]), 2)
        self.assertEqual(
            reply_markup.inline_keyboard[0][0].text,
            request_data_keyboard.rows[0][0].text,
        )

        keyboard_last_button: InlineKeyboardButton = request_data_keyboard.rows[0][1]
        reply_markup_last_button: aiogram.types.InlineKeyboardButton = (
            reply_markup.inline_keyboard[0][1]
        )

        self.assertEqual(reply_markup_last_button.text, keyboard_last_button.text)
        self.assertEqual(reply_markup_last_button.url, keyboard_last_button.url)

    def test_send_message_with_all_options(self) -> None:
        request_data_link_preview_options: LinkPreviewOptions = LinkPreviewOptions(
            is_disabled=False,
            url='https://example.com/preview/',
            prefer_small_media=False,
            prefer_large_media=True,
            show_above_text=True,
        )
        request_data_keyboard: DefaultKeyboard = DefaultKeyboard(
            rows=[
                [DefaultKeyboardButton(text='Test', style=KeyboardButtonStyle.SUCCESS)]
            ]
        )
        request_data: SendTelegramMessageRequest = SendTelegramMessageRequest(
            chat_ids=[1],
            text='<b>Important!</b>',
            text_type=TextType.HTML,
            link_preview_options=request_data_link_preview_options,
            default_keyboard=request_data_keyboard,
            disable_notification=True,
            protect_content=True,
        )

        response: httpx.Response = self.client.post(
            '/send-telegram-message/',
            headers={'X-API-KEY': APP_TOKEN},
            json=request_data.model_dump(),
        )
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.mock_bot_send_message.assert_awaited_once()

        call_kwargs: Mapping[str, Any] = self.mock_bot_send_message.call_args.kwargs
        self.assertEqual(call_kwargs['chat_id'], request_data.chat_ids[0])
        self.assertEqual(call_kwargs['text'], request_data.text)
        self.assertEqual(call_kwargs['parse_mode'], aiogram.enums.ParseMode.HTML)
        self.assertTrue(call_kwargs['disable_notification'])
        self.assertTrue(call_kwargs['protect_content'])

        link_preview_options: aiogram.types.LinkPreviewOptions = call_kwargs[
            'link_preview_options'
        ]
        self.assertFalse(link_preview_options.is_disabled)
        self.assertEqual(
            link_preview_options.url, request_data_link_preview_options.url
        )
        self.assertFalse(link_preview_options.prefer_small_media)
        self.assertTrue(link_preview_options.prefer_large_media)
        self.assertTrue(link_preview_options.show_above_text)
