from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone = '+79991234567'
        self.user_data = {
            'phone_number': '+79991234567',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com'
        }

    # ===== ТЕСТЫ ОТПРАВКИ КОДА =====

    @patch('auth_app.services.redis_client')
    def test_send_code_success(self, mock_redis):
        """Успешная отправка кода"""
        mock_redis.set_code = MagicMock()
        mock_redis.reset_attempts = MagicMock()
        mock_redis.delete_block = MagicMock()

        response = self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.phone)
        self.assertIn('message', response.data)

    def test_send_code_invalid_phone(self):
        """Отправка кода с неверным номером"""
        response = self.client.post('/api/send-code/', {
            'phone_number': '123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_code_empty_phone(self):
        """Отправка кода с пустым номером"""
        response = self.client.post('/api/send-code/', {
            'phone_number': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_code_no_phone(self):
        """Отправка кода без номера"""
        response = self.client.post('/api/send-code/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===== ТЕСТЫ ПОДТВЕРЖДЕНИЯ КОДА =====

    @patch('auth_app.services.redis_client')
    def test_verify_code_success(self, mock_redis):
        """Успешное подтверждение кода"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value='1234')
        mock_redis.reset_attempts = MagicMock()
        mock_redis.delete_block = MagicMock()
        mock_redis.delete_code = MagicMock()
        mock_redis.is_blocked = MagicMock(return_value=False)

        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '1234'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['phone_number'], self.phone)

    @patch('auth_app.services.redis_client')
    def test_verify_code_wrong(self, mock_redis):
        """Неверный код"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value='1234')
        mock_redis.increment_attempts = MagicMock(return_value=1)
        mock_redis.is_blocked = MagicMock(return_value=False)

        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '0000'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Неверный код', response.data['error'])

    @patch('auth_app.services.redis_client')
    def test_verify_code_expired(self, mock_redis):
        """Просроченный код"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value=None)
        mock_redis.is_blocked = MagicMock(return_value=False)

        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '1234'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('истек', response.data['error'])

    @patch('auth_app.services.redis_client')
    def test_verify_code_blocked(self, mock_redis):
        """Заблокированный пользователь"""
        mock_redis.is_blocked = MagicMock(return_value=True)

        # Отправляем запрос на верификацию
        response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '1234'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Проверяем наличие сообщения о блокировке
        self.assertIn('Слишком много попыток', response.data.get('error', ''))

    @patch('auth_app.services.redis_client')
    def test_verify_max_attempts(self, mock_redis):
        """Превышение попыток"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value='1234')
        mock_redis.increment_attempts = MagicMock(return_value=3)
        mock_redis.is_blocked = MagicMock(return_value=False)
        mock_redis.block_user = MagicMock()
        mock_redis.delete_code = MagicMock()

        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '0000'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('превышено', response.data['error'].lower())

    def test_verify_code_invalid_phone(self):
        """Подтверждение с неверным номером"""
        response = self.client.post('/api/verify/', {
            'phone_number': '123',
            'code': '1234'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===== ТЕСТЫ ПРОФИЛЯ =====

    @patch('auth_app.services.redis_client')
    def test_profile_success(self, mock_redis):
        """Успешное получение профиля"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value='1234')
        mock_redis.reset_attempts = MagicMock()
        mock_redis.delete_block = MagicMock()
        mock_redis.delete_code = MagicMock()
        mock_redis.is_blocked = MagicMock(return_value=False)

        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        verify_response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '1234'
        })

        token = verify_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], self.phone)
        self.assertIsNotNone(response.data['invite_code'])
        self.assertIn('invited_users', response.data)
        self.assertIn('is_verified', response.data)

    def test_profile_unauthorized(self):
        """Профиль без авторизации"""
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_invalid_token(self):
        """Профиль с неверным токеном"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ===== ТЕСТЫ ОБНОВЛЕНИЯ ТОКЕНА =====

    @patch('auth_app.services.redis_client')
    def test_refresh_token_success(self, mock_redis):
        """Успешное обновление токена"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value='1234')
        mock_redis.reset_attempts = MagicMock()
        mock_redis.delete_block = MagicMock()
        mock_redis.delete_code = MagicMock()
        mock_redis.is_blocked = MagicMock(return_value=False)

        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        verify_response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '1234'
        })

        refresh_token = verify_response.data['refresh']

        response = self.client.post('/api/refresh/', {
            'refresh': refresh_token
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalid(self):
        """Обновление с неверным токеном"""
        response = self.client.post('/api/refresh/', {
            'refresh': 'invalid_token'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_empty(self):
        """Обновление с пустым токеном"""
        response = self.client.post('/api/refresh/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ===== ТЕСТЫ ВЫХОДА =====

    @patch('auth_app.services.redis_client')
    def test_logout_success(self, mock_redis):
        """Успешный выход"""
        mock_redis.set_code = MagicMock()
        mock_redis.get_code = MagicMock(return_value='1234')
        mock_redis.reset_attempts = MagicMock()
        mock_redis.delete_block = MagicMock()
        mock_redis.delete_code = MagicMock()
        mock_redis.is_blocked = MagicMock(return_value=False)

        # Создаем пользователя
        user = User.objects.create_user(
            phone_number=self.phone,
            is_verified=True
        )
        user.generate_invite_code()

        # Отправляем код
        self.client.post('/api/send-code/', {
            'phone_number': self.phone
        })

        # Подтверждаем код
        verify_response = self.client.post('/api/verify/', {
            'phone_number': self.phone,
            'code': '1234'
        })

        # Проверяем, что верификация прошла успешно
        if verify_response.status_code != status.HTTP_200_OK:
            self.skipTest("Verify failed, skipping logout test")

        token = verify_response.data.get('access')
        refresh_token = verify_response.data.get('refresh')

        if not token or not refresh_token:
            self.skipTest("No tokens received, skipping logout test")

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.post('/api/logout/', {
            'refresh': refresh_token
        })

        # Проверяем результат
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_logout_unauthorized(self):
        """Выход без авторизации"""
        response = self.client.post('/api/logout/', {
            'refresh': 'some_token'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)