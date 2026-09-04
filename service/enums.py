from enum import StrEnum


class InvoiceType(StrEnum):
    PREMIUM = 'premium'


class InvoiceStatus(StrEnum):
    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    EXPIRED = 'expired'
    REFUNDED = 'refunded'
