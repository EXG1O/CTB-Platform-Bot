from bot.flags import auth_not_required
from bot.middlewares import UserMiddleware

from ..base import TELEGRAM_USER
from .base import MiddlewareTestCase


class UserMiddlewareTestCase(MiddlewareTestCase):
    def test_skip_creation_with_auth_not_required(self) -> None:
        self.feed_through_middlewares(
            middlewares=[UserMiddleware()], flags=[auth_not_required]
        )

        self.assertEqual(len(self.handler_calls), 1)
        self.mock_service_client.create_user.assert_not_awaited()

    def test_create_user(self) -> None:
        self.feed_through_middlewares(middlewares=[UserMiddleware()])

        self.assertEqual(len(self.handler_calls), 1)
        self.mock_service_client.create_user.assert_awaited_once_with(
            telegram_id=TELEGRAM_USER.id,
            first_name=TELEGRAM_USER.first_name,
            last_name=TELEGRAM_USER.last_name,
        )
