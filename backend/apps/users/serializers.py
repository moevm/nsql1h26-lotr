from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from apps.users.models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''
    Extends the default JWT pair serializer to embed `role` in the token
    payload.

    Configured in settings.SIMPLE_JWT['TOKEN_OBTAIN_SERIALIZER']
    '''

    @classmethod
    def get_token(cls, user: User) -> Token:  # type: ignore[override]
        token = super().get_token(user)
        token['role'] = user.role

        return token


class RegisterSerializer(serializers.Serializer):
    '''
    Validates and created a new viewer-role user.
    '''

    username = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, default='')

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                'A user with this username already exists.'
            )

        return value

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

        return value

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            role=User.Role.VIEWER,
        )


class UserProfileSerializer(serializers.Serializer):
    '''
    Read/write serializer for current user's profile. Role is intentionally
    read only, for only an admin can change it in the DB so far

    TODO: add ability to promote users to admin role or something like that
    '''

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(read_only=True)

    def update(self, instance: User, validated_data: dict) -> User:
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get(
            'first_name', instance.first_name
        )
        instance.last_name = validated_data.get(
            'last_name', instance.last_name
        )

        instance.save(update_fields=['email', 'first_name', 'last_name'])

        return instance


class LogoutSerializer(serializers.Serializer):
    '''The client must senf its current refresh token to be blacklisted'''

    refresh = serializers.CharField()


class TokenPairSerializer(serializers.Serializer):
    '''
    Schema-only serializer.
    Describes the login/refresh response for Swagger.
    '''

    access = serializers.CharField()
    refresh = serializers.CharField()
