from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import InputFile

from aiolimiter import AsyncLimiter
import httpx
import orjson

from core.settings import USER_AGENT

from collections.abc import AsyncGenerator
from typing import Any, cast
import asyncio
import logging

logger = logging.getLogger(__name__)


class Session(BaseSession):
    def __init__(self) -> None:
        super().__init__(
            json_loads=orjson.loads,
            json_dumps=lambda data: orjson.dumps(data).decode(),
        )

        self._client = httpx.AsyncClient(
            headers={'User-Agent': USER_AGENT},
            transport=httpx.AsyncHTTPTransport(
                trust_env=False,
                http2=True,
                limits=httpx.Limits(
                    max_connections=30,
                    max_keepalive_connections=10,
                    keepalive_expiry=30,
                ),
                retries=2,
            ),
        )

        self._global_limiter = AsyncLimiter(max_rate=30, time_period=1)
        self._user_limiters: dict[int, AsyncLimiter] = {}
        self._group_limiters: dict[int, AsyncLimiter] = {}

    async def close(self) -> None:
        await self._client.aclose()

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

        url: str = self.api.api_url(token=bot.token, method=method.__api_method__)
        data: dict[str, Any] = {}
        files: dict[str, tuple[str, bytes]] = {}

        raw_files: dict[str, InputFile] = {}

        for key, value in method.model_dump(warnings=False).items():
            value = self.prepare_value(value, bot=bot, files=raw_files)
            if not value:
                continue
            data[key] = value

        for key, value in raw_files.items():
            files[key] = (
                value.filename or key,
                # FIXME: In the future, files need to be saved in temporary directories.
                b''.join([chunk async for chunk in value.read(bot)]),
            )

        while True:
            response: httpx.Response = await self._client.post(
                url, data=data, files=files, timeout=timeout or self.timeout
            )

            try:
                return cast(
                    TelegramType,
                    self.check_response(
                        bot=bot,
                        method=method,
                        status_code=response.status_code,
                        content=response.text,
                    ).result,
                )
            except TelegramRetryAfter as error:
                logger.debug(
                    'Rate limited. Retrying after %d seconds', error.retry_after
                )
                await asyncio.sleep(error.retry_after)
                continue

    async def stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: int = 30,  # noqa: ASYNC109
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes]:
        if headers is None:
            headers = {}

        response: httpx.Response = await self._client.get(
            url, headers=headers, timeout=timeout
        )

        if raise_for_status:
            response.raise_for_status()

        async for chunk in response.aiter_bytes(chunk_size):
            yield chunk
