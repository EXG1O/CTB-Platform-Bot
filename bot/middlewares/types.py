from aiogram.dispatcher.middlewares.data import MiddlewareData as BaseMiddlewareData

import service

from ..models import User


class MiddlewareData(BaseMiddlewareData, total=False):
    service_client: service.Client
    user: User
