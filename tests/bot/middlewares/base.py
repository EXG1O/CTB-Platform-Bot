from aiogram import BaseMiddleware, Dispatcher, Router
from aiogram.dispatcher.flags import FlagDecorator
from aiogram.types import Message

from ..base import BotTestCase


class MiddlewareTestCase(BotTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.handler_calls: list[Message] = []

    def feed_through_middlewares(
        self,
        middlewares: list[BaseMiddleware],
        flags: list[FlagDecorator] | None = None,
    ) -> None:
        router: Router = Router()

        async def handler(message: Message) -> None:
            self.handler_calls.append(message)

        if flags:
            for flag in flags:
                flag(handler)

        router.message.register(handler)

        self.dispatcher = Dispatcher(service_client=self.mock_service_client)

        for middleware in middlewares:
            self.dispatcher.message.middleware(middleware)

        self.dispatcher.include_router(router)
        self.feed_message()
