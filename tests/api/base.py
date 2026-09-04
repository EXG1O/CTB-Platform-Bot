from fastapi.testclient import TestClient

from main import app

from ..base import BaseTestCase


class APITestCase(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = TestClient(app)
