from django.conf import settings


class MockRedisClient:
    """Мок для Redis, используемый в тестах"""

    def __init__(self):
        self.data = {}
        self.ttl = {}

    def set_code(self, phone_number, code):
        key = f"code:{phone_number}"
        self.data[key] = code
        self.ttl[key] = settings.VERIFICATION_CODE_TTL

    def get_code(self, phone_number):
        key = f"code:{phone_number}"
        return self.data.get(key)

    def delete_code(self, phone_number):
        key = f"code:{phone_number}"
        self.data.pop(key, None)
        self.ttl.pop(key, None)

    def increment_attempts(self, phone_number):
        key = f"attempts:{phone_number}"
        attempts = self.data.get(key, 0) + 1
        self.data[key] = attempts
        return attempts

    def reset_attempts(self, phone_number):
        key = f"attempts:{phone_number}"
        self.data.pop(key, None)

    def is_blocked(self, phone_number):
        key = f"blocked:{phone_number}"
        return key in self.data

    def block_user(self, phone_number):
        key = f"blocked:{phone_number}"
        self.data[key] = True

    def delete_block(self, phone_number):
        key = f"blocked:{phone_number}"
        self.data.pop(key, None)


mock_redis = MockRedisClient()
