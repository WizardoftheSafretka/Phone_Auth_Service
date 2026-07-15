import os
import sys

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from test_redis_client import mock_redis

User = get_user_model()


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone = "+79991234567"
        # Очищаем мок перед каждым тестом
        mock_redis.data.clear()
        mock_redis.ttl.clear()

    def test_send_code(self):
        response = self.client.post("/api/send-code/", {"phone_number": self.phone})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone_number"], self.phone)

    def test_verify_code(self):
        # Сначала отправляем код
        self.client.post("/api/send-code/", {"phone_number": self.phone})

        # Получаем код из мока
        code = mock_redis.get_code(self.phone)
        self.assertIsNotNone(code)

        # Подтверждаем
        response = self.client.post(
            "/api/verify/", {"phone_number": self.phone, "code": code}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_wrong_code(self):
        self.client.post("/api/send-code/", {"phone_number": self.phone})

        response = self.client.post(
            "/api/verify/", {"phone_number": self.phone, "code": "0000"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Неверный код", response.data["error"])

    def test_profile(self):
        # Регистрируемся
        self.client.post("/api/send-code/", {"phone_number": self.phone})
        code = mock_redis.get_code(self.phone)
        verify_response = self.client.post(
            "/api/verify/", {"phone_number": self.phone, "code": code}
        )

        token = verify_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get("/api/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone_number"], self.phone)
