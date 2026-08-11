from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader

from core.settings import APP_TOKEN, TELEGRAM_TOKEN

from typing import Annotated
import secrets

telegram_token_header = APIKeyHeader(name='X-Telegram-Bot-Api-Secret-Token')
app_token_header = APIKeyHeader(name='X-API-KEY')


async def verify_telegram_token(
    token: Annotated[str, Depends(telegram_token_header)],
) -> str:
    if not secrets.compare_digest(token, TELEGRAM_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token


async def verify_app_token(token: Annotated[str, Depends(app_token_header)]) -> str:
    if not secrets.compare_digest(token, APP_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token
