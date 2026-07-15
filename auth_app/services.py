import random
import logging
import time
from users.models import CustomUser
from .redis_client import redis_client

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def generate_code():
        return str(random.randint(1000, 9999))

    @staticmethod
    def send_verification_code(phone_number):
        phone_number = CustomUser.objects.normalize_phone_number(phone_number)
        code = AuthService.generate_code()

        time.sleep(random.uniform(1.0, 2.0))

        redis_client.set_code(phone_number, code)
        redis_client.reset_attempts(phone_number)
        redis_client.delete_block(phone_number)

        logger.info(f"VERIFICATION CODE for {phone_number}: {code}")
        return code

    @staticmethod
    def verify_code(phone_number, code):
        phone_number = CustomUser.objects.normalize_phone_number(phone_number)

        if redis_client.is_blocked(phone_number):
            return False, "Слишком много попыток. Попробуйте через 5 минут"

        stored_code = redis_client.get_code(phone_number)

        if not stored_code:
            return False, "Код истек. Запросите новый"

        if stored_code != code:
            attempts = redis_client.increment_attempts(phone_number)
            remaining = 3 - attempts
            if attempts >= 3:
                redis_client.block_user(phone_number)
                redis_client.delete_code(phone_number)
                return False, "Превышено количество попыток. Блокировка на 5 минут"
            return False, f"Неверный код. Осталось попыток: {remaining}"

        redis_client.delete_code(phone_number)
        redis_client.reset_attempts(phone_number)
        redis_client.delete_block(phone_number)
        return True, "Код подтвержден"

    @staticmethod
    def get_or_create_user(phone_number):
        phone_number = CustomUser.objects.normalize_phone_number(phone_number)

        user, created = CustomUser.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'is_active': True,
                'is_verified': False,
            }
        )

        if created:
            user.generate_invite_code()

        return user, created

    @staticmethod
    def activate_invite_code(user, invite_code):
        return user.activate_invite_code(invite_code)

    @staticmethod
    def get_user_profile(user):
        return user.get_profile()