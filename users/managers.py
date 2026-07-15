import re

from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Кастомный юзер-менеджер"""

    def create_user(self, phone_number, password=None, **extra_fields):
        """
        Создание обычного пользователя с автоматической генерацией инвайт-кода
        """
        if not phone_number:
            raise ValueError("Номер телефона обязателен")

        phone_number = self.normalize_phone_number(phone_number)

        # Устанавливаем значения по умолчанию
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", False)

        user = self.model(phone_number=phone_number, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)

        # Генерируем инвайт-код после сохранения
        if not user.invite_code:
            user.generate_invite_code()

        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """
        Создание суперпользователя
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)

    def normalize_phone_number(self, phone_number):
        """
        Нормализация номера телефона: удаление пробелов и спецсимволов,
        добавление + если отсутствует
        """
        cleaned = re.sub(r"[\s\-\(\)]", "", phone_number)
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return cleaned

    def get_by_invite_code(self, invite_code):
        """Получение пользователя по инвайт-коду"""
        try:
            return self.get(invite_code=invite_code)
        except self.model.DoesNotExist:
            return None

    def get_with_profile(self, phone_number):
        """
        Получение пользователя с предзагрузкой связанных данных для профиля
        """
        try:
            return (
                self.select_related("activated_invite_code")
                .prefetch_related("invited_users")
                .get(phone_number=phone_number)
            )
        except self.model.DoesNotExist:
            return None
