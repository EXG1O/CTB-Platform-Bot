from httpcore import AsyncConnectionPool, Response
from yarl import URL
import msgspec

from core.exceptions import HTTPError
from core.msgspec import json_encoder
from core.settings import SERVICE_SOCKET, SERVICE_TOKEN, SERVICE_URL, USER_AGENT

from typing import Any, Final, overload
import logging

logger = logging.getLogger(__name__)

ROOT_URL: Final[URL] = SERVICE_URL / 'api' / 'platform-bot/'
HEADERS: Final[dict[bytes | str, bytes | str]] = {
    b'User-Agent': USER_AGENT.encode(),
    b'Content-Type': b'application/json',
    b'Authorization': f'Token {SERVICE_TOKEN}'.encode(),
}


class ServiceClient:
    def __init__(self) -> None:
        self._pool = AsyncConnectionPool(
            max_connections=25,
            max_keepalive_connections=10,
            keepalive_expiry=12,
            uds=str(SERVICE_SOCKET) if SERVICE_SOCKET else None,
        )

    async def close(self) -> None:
        await self._pool.aclose()

    @overload
    async def _request[T](
        self,
        method: str,
        url: str,
        decoder: msgspec.json.Decoder[T],
        data: Any | None = None,
    ) -> T: ...

    @overload
    async def _request(
        self,
        method: str,
        url: str,
        decoder: None = None,
        data: Any | None = None,
    ) -> None: ...

    async def _request[T](
        self,
        method: str,
        url: str,
        decoder: msgspec.json.Decoder[T] | None = None,
        data: Any | None = None,
    ) -> T | None:
        try:
            response: Response = await self._pool.request(
                method,
                url,
                headers=HEADERS,
                content=json_encoder.encode(data) if data is not None else None,
            )

            if response.status >= 400:
                raise HTTPError(response)  # noqa: TRY301
        except Exception as error:
            logger.exception('Failed request to the main service')
            raise error
        else:
            if not decoder:
                return None
            return decoder.decode(response.content)
