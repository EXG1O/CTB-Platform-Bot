import httpx
import orjson

from core.settings import SERVICE_SOCKET, SERVICE_TOKEN, SERVICE_URL, USER_AGENT

from .enums import InvoiceStatus, InvoiceType
from .models import Invoice, ServiceObject, User

from http import HTTPMethod
from typing import Any, overload
import logging

logger = logging.getLogger(__name__)


class Client:
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
                retries=2,
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
        except httpx.HTTPError:
            logger.exception('Failed request to the main service.')
            raise
        else:
            if not response_model:
                return None
            return response_model.model_validate_json(response.content)

    async def create_user(
        self, telegram_id: int, first_name: str, last_name: str | None
    ) -> User:
        return await self._request(
            HTTPMethod.POST,
            '/users/',
            json={
                'telegram_id': telegram_id,
                'first_name': first_name,
                'last_name': last_name,
            },
            response_model=User,
        )

    async def create_invoice(
        self, user_id: int, type: InvoiceType, period_months: int, amount_stars: int
    ) -> Invoice:
        return await self._request(
            HTTPMethod.POST,
            f'/users/{user_id}/{type}/invoices/',
            json={'period_months': period_months, 'amount_stars': amount_stars},
            response_model=Invoice,
        )

    async def get_invoice(self, id: int, user_id: int, type: InvoiceType) -> Invoice:
        return await self._request(
            HTTPMethod.POST,
            f'/users/{user_id}/{type}/invoices/',
            response_model=Invoice,
        )

    async def update_invoice_status(
        self,
        id: int,
        user_id: int,
        type: InvoiceType,
        status: InvoiceStatus,
        telegram_charge_id: str | None = None,
    ) -> Invoice:
        data: dict[str, Any] = {'status': status}

        if status == InvoiceStatus.PAID:
            if not telegram_charge_id:
                raise ValueError(
                    'telegram_charge_id is required when status is InvoiceStatus.PAID.'
                )
            data['telegram_charge_id'] = telegram_charge_id

        return await self._request(
            HTTPMethod.PATCH,
            f'/users/{user_id}/{type}/invoices/{id}/',
            json=data,
            response_model=Invoice,
        )
