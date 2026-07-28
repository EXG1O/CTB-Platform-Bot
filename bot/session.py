from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType

from aiohttp import ClientSession, ClientTimeout, FormData, hdrs
from aiohttp.typedefs import LooseHeaders
from aiolimiter import AsyncLimiter

from core.msgspec import json_decoder, json_encoder
from core.settings import USER_AGENT

from typing import Final, cast
import asyncio
import logging

logger = logging.getLogger(__name__)

HEADERS: Final[LooseHeaders] = {hdrs.USER_AGENT: USER_AGENT}


class Session(AiohttpSession):
    def __init__(self) -> None:
        super().__init__(
            json_loads=json_decoder.decode,
            json_dumps=lambda data: json_encoder.encode(data).decode(),
        )

        self._global_limiter = AsyncLimiter(max_rate=30, time_period=1)
        self._user_limiters: dict[int, AsyncLimiter] = {}
        self._group_limiters: dict[int, AsyncLimiter] = {}

    def _get_chat_limiter(self, chat_id: int) -> AsyncLimiter:
        if chat_id > 0:
            return self._user_limiters.setdefault(
                chat_id, AsyncLimiter(max_rate=1, time_period=1)
            )

        return self._group_limiters.setdefault(
            chat_id, AsyncLimiter(max_rate=20, time_period=60)
        )

    async def _acquire_rate_limit(self, chat_id: int | None = None) -> None:
        if chat_id is not None:
            async with self._get_chat_limiter(chat_id), self._global_limiter:
                return

        async with self._global_limiter:
            return

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,  # noqa: ASYNC109
    ) -> TelegramType:
        chat_id: int | None = getattr(method, 'chat_id', None)
        await self._acquire_rate_limit(chat_id)

        session: ClientSession = await self.create_session()
        url: str = self.api.api_url(token=bot.token, method=method.__api_method__)
        form: FormData = self.build_form_data(bot=bot, method=method)
        request_timeout = ClientTimeout(
            total=self.timeout if timeout is None else timeout
        )

        while True:
            async with session.post(
                url, data=form, headers=HEADERS, timeout=request_timeout
            ) as response:
                body: str = await response.text()

            try:
                return cast(
                    TelegramType,
                    self.check_response(
                        bot=bot,
                        method=method,
                        status_code=response.status,
                        content=body,
                    ).result,
                )
            except TelegramRetryAfter as error:
                logger.debug(
                    'Rate limited. Retrying after %d seconds', error.retry_after
                )
                await asyncio.sleep(error.retry_after)
                continue
