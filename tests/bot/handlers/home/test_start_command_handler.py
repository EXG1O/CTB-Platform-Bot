from aiogram.methods import SendMessage

from bot.handlers.home.data import WELCOME_TEXT

from ...base import TELEGRAM_USER, BotTestCase


class StartCommandHandlerTestCase(BotTestCase):
    def test_send_welcome_message(self) -> None:
        self.feed_command('/start')

        requests: list[SendMessage] = self.get_requests(SendMessage)
        self.assertEqual(len(requests), 1)

        message: SendMessage = requests[0]
        self.assertEqual(
            message.text, WELCOME_TEXT.format(user_full_name=TELEGRAM_USER.full_name)
        )
