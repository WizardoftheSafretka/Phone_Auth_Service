import random
import string

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models, transaction

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Модель пользователя"""

    phone_regex = RegexValidator(
        regex=r"^\+\d{10,15}$", message="Номер должен быть в формате: +79991234567"
    )

    phone_number = models.CharField(
        max_length=16,
        unique=True,
        validators=[phone_regex],
        verbose_name="Номер телефона",
        db_index=True,
    )

    invite_code = models.CharField(
        max_length=6,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Инвайт-код",
        db_index=True,
    )

    activated_invite_code = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invited_users",
        verbose_name="Активированный инвайт-код",
        db_index=True,
    )

    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_verified = models.BooleanField(default=False, verbose_name="Подтвержден")
    is_staff = models.BooleanField(default=False, verbose_name='Персонал')

    date_joined = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )
    last_login = models.DateTimeField(
        null=True, blank=True, verbose_name="Последний вход"
    )

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.phone_number}"

    def generate_invite_code(self):
        """Генерация уникального инвайт-кода с транзакционной безопасностью"""
        chars = string.digits + string.ascii_uppercase

        with transaction.atomic():
            # Блокируем запись для избежания гонки состояний
            user = CustomUser.objects.select_for_update().get(pk=self.pk)

            for _ in range(100):  # Лимит попыток
                code = "".join(random.choices(chars, k=6))
                if not CustomUser.objects.filter(invite_code=code).exists():
                    user.invite_code = code
                    user.save(update_fields=["invite_code"])
                    return code

            raise RuntimeError("Не удалось сгенерировать уникальный инвайт-код")

    def activate_invite_code(self, invite_code):
        """
        Активация инвайт-кода

        Returns:
            tuple: (success: bool, message: str)
        """
        # Проверка на уже активированный код
        if self.activated_invite_code_id:
            return False, "Вы уже активировали инвайт-код"

        # Проверка формата
        if not invite_code or len(invite_code) != 6:
            return False, "Неверный формат инвайт-кода"

        # Проверка на собственный код
        if self.invite_code == invite_code:
            return False, "Нельзя активировать свой код"

        # Поиск реферера
        try:
            referrer = CustomUser.objects.get(invite_code=invite_code)
        except CustomUser.DoesNotExist:
            return False, "Инвайт-код не найден"

        # Активация
        self.activated_invite_code = referrer
        self.save(update_fields=["activated_invite_code"])
        return True, "Инвайт-код активирован"

    def get_invited_phones(self):
        """Получение списка телефонов приглашенных пользователей"""
        return self.invited_users.values_list("phone_number", flat=True)

    def get_profile(self, prefetch=False):
        """
        Получение профиля пользователя

        Args:
            prefetch: bool - если True, использует предварительно загруженные данные
        """
        profile = {
            "phone_number": self.phone_number,
            "invite_code": self.invite_code,
            "activated_invite_code": None,
            "invited_users": [],
            "is_verified": self.is_verified,
            "date_joined": self.date_joined,
        }

        # Активированный код
        if self.activated_invite_code_id:
            if prefetch and hasattr(self, "_prefetched_objects_cache"):
                profile["activated_invite_code"] = (
                    self.activated_invite_code.invite_code
                )
            else:
                # Ленивая загрузка
                try:
                    profile["activated_invite_code"] = (
                        self.activated_invite_code.invite_code
                    )
                except CustomUser.DoesNotExist:
                    pass

        # Приглашенные пользователи
        if prefetch and hasattr(self, "_prefetched_objects_cache"):
            profile["invited_users"] = list(
                self.invited_users.values_list("phone_number", flat=True)
            )
        else:
            profile["invited_users"] = list(self.get_invited_phones())

        return profile
