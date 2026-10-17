from aiogram.methods import SendMessage

from bot.flags import accepted_terms_not_required, auth_not_required
from bot.middlewares import UserMiddleware, UserTermsCheckMiddleware
from bot.middlewares.user_terms_check import TEXT

from ..base import TELEGRAM_USER
from .base import MiddlewareTestCase


class UserTermsCheckMiddlewareTestCase(MiddlewareTestCase):
    def test_send_message_without_accepted_terms(self) -> None:
        self.set_accepted_terms(accepted_terms=False)
        self.feed_through_middlewares(
            middlewares=[UserMiddleware(), UserTermsCheckMiddleware()]
        )

        self.assertEqual(self.handler_calls, [])

        requests: list[SendMessage] = self.get_requests(SendMessage)
        self.assertEqual(len(requests), 1)

        message: SendMessage = requests[0]
        self.assertEqual(message.chat_id, TELEGRAM_USER.id)
        self.assertEqual(message.text, TEXT)

    def test_skip_terms_check_with_auth_not_required(self) -> None:
        self.set_accepted_terms(accepted_terms=False)
        self.feed_through_middlewares(
            middlewares=[UserMiddleware(), UserTermsCheckMiddleware()],
            flags=[auth_not_required],
        )

        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(self.get_requests(SendMessage), [])

    def test_skip_terms_check_with_terms_not_required(self) -> None:
        self.set_accepted_terms(accepted_terms=False)
        self.feed_through_middlewares(
            middlewares=[UserMiddleware(), UserTermsCheckMiddleware()],
            flags=[accepted_terms_not_required],
        )

        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(self.get_requests(SendMessage), [])

    def test_pass_through_with_accepted_terms(self) -> None:
        self.feed_through_middlewares(
            middlewares=[UserMiddleware(), UserTermsCheckMiddleware()]
        )

        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(self.get_requests(SendMessage), [])
