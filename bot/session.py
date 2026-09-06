from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramRetryAfter
from aiogram.methods import TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import InputFile

import httpx
import orjson

from core.settings import USER_AGENT

from .limiter import Limiter

from collections.abc import AsyncGenerator
from typing import Any, cast
import asyncio
import logging

logger = logging.getLogger(__name__)


class Session(BaseSession):
    def __init__(self, limiter: Limiter) -> None:
        super().__init__(
            json_loads=orjson.loads,
            json_dumps=lambda data: orjson.dumps(data).decode(),
        )

        self._limiter = limiter
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

    async def close(self) -> None:
        await self._client.aclose()

    async def make_request(
        self,
        bot: Bot,
        method: TelegramMethod[TelegramType],
        timeout: int | None = None,  # noqa: ASYNC109
    ) -> TelegramType:
        chat_id: int | None = getattr(method, 'chat_id', None)
        await self._limiter.acquire(chat_id)

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
                    'Rate limited. Retrying after %d seconds.', error.retry_after
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
