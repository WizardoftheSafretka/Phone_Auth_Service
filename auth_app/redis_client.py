import redis
from django.conf import settings


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def set_code(self, phone_number, code):
        key = f"code:{phone_number}"
        self.client.setex(key, settings.VERIFICATION_CODE_TTL, code)

    def get_code(self, phone_number):
        key = f"code:{phone_number}"
        return self.client.get(key)

    def delete_code(self, phone_number):
        key = f"code:{phone_number}"
        self.client.delete(key)

    def increment_attempts(self, phone_number):
        key = f"attempts:{phone_number}"
        attempts = self.client.incr(key)
        if attempts == 1:
            self.client.expire(key, settings.BLOCK_DURATION)
        return attempts

    def reset_attempts(self, phone_number):
        key = f"attempts:{phone_number}"
        self.client.delete(key)

    def is_blocked(self, phone_number):
        key = f"blocked:{phone_number}"
        return self.client.exists(key) == 1

    def block_user(self, phone_number):
        key = f"blocked:{phone_number}"
        self.client.setex(key, settings.BLOCK_DURATION, "blocked")

    def delete_block(self, phone_number):
        key = f"blocked:{phone_number}"
        self.client.delete(key)


redis_client = RedisClient()