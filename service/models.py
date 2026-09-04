from pydantic import BaseModel

from .enums import InvoiceStatus


class ServiceObject(BaseModel):
    pass


class User(ServiceObject):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    accepted_terms: bool


class Invoice(ServiceObject):
    id: int
    status: InvoiceStatus
    period_months: int
    amount_stars: int
    telegram_charge_id: str | None
