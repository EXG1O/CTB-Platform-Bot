import aiogram

from pydantic import BaseModel

import service


class User(BaseModel):
    telegram: aiogram.types.User
    service: service.User


class InvoicePayload(BaseModel):
    id: int
