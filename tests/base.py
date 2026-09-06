from unittest.mock import AsyncMock, patch
import unittest


class BaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.patcher_bot = patch('bot.bot', new_callable=AsyncMock)
        self.patcher_service_client = patch(
            'bot.service_client', new_callable=AsyncMock
        )

        self.mock_bot = self.patcher_bot.start()
        self.mock_service_client = self.patcher_service_client.start()

    def tearDown(self) -> None:
        self.patcher_bot.stop()
        self.patcher_service_client.stop()
