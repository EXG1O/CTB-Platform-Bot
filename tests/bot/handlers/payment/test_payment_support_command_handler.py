from aiogram.methods import SendMessage

from bot.handlers.payment.data import PAYMENT_SUPPORT_TEXT

from ...base import BotTestCase


class PaymentSupportCommandHandlerTestCase(BotTestCase):
    def test_send_support_message(self) -> None:
        self.feed_command('/paysupport')

        requests: list[SendMessage] = self.get_requests(SendMessage)
        self.assertEqual(len(requests), 1)

        message: SendMessage = requests[0]
        self.assertEqual(message.text, PAYMENT_SUPPORT_TEXT)
