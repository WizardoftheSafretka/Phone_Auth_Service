from django.core.validators import RegexValidator
from rest_framework import serializers


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=16,
        validators=[
            RegexValidator(regex=r"^\+\d{10,15}$", message="Формат: +79991234567")
        ],
    )


class VerifySerializer(PhoneNumberSerializer):
    code = serializers.CharField(max_length=4, min_length=4)


class ActivateInviteSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6, min_length=6)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
