import httpx
import orjson

from core.settings import SERVICE_SOCKET, SERVICE_TOKEN, SERVICE_URL, USER_AGENT

from .models import ServiceObject

from http import HTTPMethod
from typing import Any, overload
import logging

logger = logging.getLogger(__name__)


class ServiceClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=str(SERVICE_URL / 'api' / 'platform-bot/'),
            headers={
                'User-Agent': USER_AGENT,
                'Authorization': f'Token {SERVICE_TOKEN}',
            },
            transport=httpx.AsyncHTTPTransport(
                trust_env=False,
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=6,
                ),
                uds=str(SERVICE_SOCKET) if SERVICE_SOCKET else None,
                retries=3,
            ),
        )

    async def close(self) -> None:
        await self._client.aclose()

    @overload
    async def _request[T: ServiceObject](
        self,
        method: HTTPMethod,
        endpoint: str,
        response_model: type[T],
        json: Any | None = None,
    ) -> T: ...

    @overload
    async def _request(
        self,
        method: HTTPMethod,
        endpoint: str,
        response_model: None = None,
        json: Any | None = None,
    ) -> None: ...

    async def _request[T: ServiceObject](
        self,
        method: HTTPMethod,
        endpoint: str,
        response_model: type[T] | None = None,
        json: Any | None = None,
    ) -> T | None:
        try:
            response: httpx.Response = await self._client.request(
                method,
                endpoint,
                headers={'Content-Type': 'application/json'},
                content=orjson.dumps(json) if json is not None else None,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            logger.exception('Failed request to the main service')
            raise error
        else:
            if not response_model:
                return None
            return response_model.model_validate_json(response.content)
