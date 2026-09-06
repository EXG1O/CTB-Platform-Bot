from aiolimiter import AsyncLimiter

from collections.abc import Awaitable
import asyncio


class Limiter:
    def __init__(self) -> None:
        self._global_limiter = AsyncLimiter(max_rate=30, time_period=1)
        self._user_limiters: dict[int, AsyncLimiter] = {}
        self._group_limiters: dict[int, AsyncLimiter] = {}
        self._external_semaphore = asyncio.Semaphore(15)

    def _get_chat_limiter(self, chat_id: int) -> AsyncLimiter:
        if chat_id > 0:
            return self._user_limiters.setdefault(
                chat_id, AsyncLimiter(max_rate=1, time_period=1)
            )

        return self._group_limiters.setdefault(
            chat_id, AsyncLimiter(max_rate=20, time_period=60)
        )

    async def acquire(self, chat_id: int | None = None) -> None:
        if chat_id is not None:
            async with self._get_chat_limiter(chat_id), self._global_limiter:
                return

        async with self._global_limiter:
            return

    async def throttle_external_call[T](self, coro: Awaitable[T]) -> T:
        async with self._external_semaphore:
            return await coro
