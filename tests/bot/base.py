from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.enums import MessageEntityType
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import Chat, Message, MessageEntity, PreCheckoutQuery, Update, User

from bot import dispatcher
import service

from ..base import BaseTestCase

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, cast, get_origin
from unittest.mock import patch
import asyncio

BOT_TOKEN: Final[str] = '123456:test'
TELEGRAM_USER_ID: Final[int] = 1
TELEGRAM_USER: Final[User] = User(id=TELEGRAM_USER_ID, is_bot=False, first_name='exg1o')
TELEGRAM_CHAT: Final[Chat] = Chat(
    id=TELEGRAM_USER_ID, type='private', first_name=TELEGRAM_USER.first_name
)

SERVICE_USER_ID: Final[int] = 1
SERVICE_INVOICE_ID: Final[int] = 1


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.requests: list[TelegramMethod[Any]] = []

    async def close(self) -> None:
        return None

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,  # noqa: ASYNC109
    ) -> TelegramType:
        self.requests.append(method)

        returning: Any = method.__returning__

        if TYPE_CHECKING:
            result: Any

        if returning is bool:
            result = True
        elif returning is Message:
            result = Message(
                message_id=1, chat=TELEGRAM_CHAT, date=datetime.fromtimestamp(0, tz=UTC)
            )
        elif get_origin(returning) is list:
            result = []
        else:
            result = returning.model_construct()

        return cast(TelegramType, result)

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,  # noqa: ASYNC109
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes]:
        yield b''


class BotTestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.session: FakeSession = FakeSession()
        self.bot: Bot = Bot(token=BOT_TOKEN, session=self.session)
        self.dispatcher: Dispatcher = dispatcher

        self.enterContext(
            patch.dict(
                dispatcher.workflow_data, {'service_client': self.mock_service_client}
            )
        )
        self.enterContext(patch.object(dispatcher.fsm, 'storage', MemoryStorage()))

        self.set_accepted_terms(accepted_terms=True)

    def set_accepted_terms(self, accepted_terms: bool) -> None:
        self.service_user: service.User = service.User(
            id=SERVICE_USER_ID,
            telegram_id=TELEGRAM_USER.id,
            first_name=TELEGRAM_USER.first_name,
            last_name=TELEGRAM_USER.last_name,
            accepted_terms=accepted_terms,
        )
        self.mock_service_client.create_user.return_value = self.service_user

    def feed(self, update: Update) -> None:
        asyncio.run(self.dispatcher.feed_update(self.bot, update))

    def feed_message(self, **kwargs: Any) -> None:
        self.feed(
            Update(
                update_id=1,
                message=Message(
                    message_id=1,
                    date=datetime.fromtimestamp(0, tz=UTC),
                    chat=TELEGRAM_CHAT,
                    from_user=TELEGRAM_USER,
                    **kwargs,
                ).as_(self.bot),
            )
        )

    def feed_command(self, command: str) -> None:
        self.feed_message(
            text=command,
            entities=[
                MessageEntity(
                    type=MessageEntityType.BOT_COMMAND, offset=0, length=len(command)
                )
            ],
        )

    def feed_pre_checkout_query(self, invoice_payload: str) -> None:
        self.feed(
            Update(
                update_id=1,
                pre_checkout_query=PreCheckoutQuery(
                    id='test',
                    from_user=TELEGRAM_USER,
                    currency='XTR',
                    total_amount=100,
                    invoice_payload=invoice_payload,
                ).as_(self.bot),
            )
        )

    def get_requests[T: TelegramMethod[Any]](self, method_type: type[T]) -> list[T]:
        return [
            request
            for request in self.session.requests
            if isinstance(request, method_type)
        ]
