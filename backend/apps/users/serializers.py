from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User

# Auth serializers (used by /auth/ endpoints)


class AuthUserSerializer(serializers.ModelSerializer):
    '''User representation for login/register response'''

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role',
            'avatar_url')
        read_only_fields = fields


class TokenPairSerializer(serializers.Serializer):
    '''
    Schema-only serializer.
    Describes the login/refresh response for Swagger.
    Flat token pair - used by RefreshView schema
    '''

    access = serializers.CharField()
    refresh = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    '''Top-level response for POST /auth/login/ and /auth/register/.'''

    user = AuthUserSerializer()
    tokens = TokenPairSerializer()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    '''
    Extends the default JWT pair serializer to embed `role` in the token
    payload.

    Configured in settings.SIMPLE_JWT['TOKEN_OBTAIN_SERIALIZER']
    '''

    @classmethod
    def get_token(cls, user: User) -> RefreshToken:  # type: ignore[override]
        token = super().get_token(user)
        token['role'] = user.role

        return token  # type: ignore[return-value]  # super() returns Token, but really a RefreshToken

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        return {
            'user': AuthUserSerializer(self.user).data,
            'tokens': {
                'access': data['access'],
                'refresh': data['refresh'],
            }
        }


class MeSerializer(serializers.ModelSerializer):
    '''
    Read-only serializer for current user GET /auth/me/.
    Liked pages are added in view.
    '''

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role',
            'avatar_url'
        )


class MePatchSerializer(serializers.Serializer):
    '''
    Partial update of current user profile.
    password requiers password_current.
    '''

    username = serializers.CharField(required=False)
    avatar_url = serializers.URLField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False)
    password_current = serializers.CharField(write_only=True, required=False)

    def validate_username(self, value: str) -> str:
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError(
                'A user with this username already exists.'
            )

        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get('password') and not attrs.get('password_current'):
            raise serializers.ValidationError(
                {
                    'password_current': [
                        'Current password is required to set a new password.'
                    ]
                }
            )
        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        if 'avatar_url' in validated_data:
            instance.avatar_url = validated_data.pop('avatar_url')

        if 'password' in validated_data:
            current = validated_data.pop('password_current', None)
            if not current or not instance.check_password(current):
                raise serializers.ValidationError(
                    {
                        'password_current': [
                            'Current password is incorrect.'
                        ]
                    }
                )
            instance.set_password(validated_data.pop('password'))
        else:
            validated_data.pop('password_current', None)

        for attr in ('username', 'email', 'first_name', 'last_name'):
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])

        instance.save()

        return instance


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


class LogoutSerializer(serializers.Serializer):
    '''The client must senf its current refresh token to be blacklisted'''

    refresh = serializers.CharField()


# User-management serializers (used by /users/* endpoints)


class PageSummarySerializer(serializers.Serializer):
    '''
    Minimal page representation returned inside user-related responses.
    '''

    slug = serializers.CharField()
    type = serializers.CharField(
        help_text='Entity type (character, race, location, ...).'
    )
    name = serializers.CharField(allow_null=True)
    image_url = serializers.CharField(allow_null=True)


class UserAdminListSerializer(serializers.ModelSerializer):
    '''
    User representation for GET /users/ (admin-only list).

    Returns all fields that an administrator needs: email, role, join date.
    '''
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'avatar_url', 'created_at')
        read_only_fields = ('username', 'email', 'role', 'avatar_url', 'created_at')


class UserPublicProfileSerializer(serializers.Serializer):
    '''
    Schema-only serializer for GET /users/{username}/.
    '''

    username = serializers.CharField()
    avatar_url = serializers.URLField(allow_null=True)
    created_at = serializers.DateTimeField()
    comments_count = serializers.IntegerField()
    liked_pages_total = serializers.IntegerField()
    liked_pages = PageSummarySerializer(many=True)


class UserRoleSerializer(serializers.ModelSerializer):
    '''
    Input serializer for PATCH /users/{username}/.
    '''

    class Meta:
        model = User
        fields = ('role',)


class PaginatedPageSummarySerializer(serializers.Serializer):
    '''
    Schema-only serializer for GET /users/{username}/liked/ response.
    Mirrors the standard PaginatedResponse + PageSummary results shape.
    '''

    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = PageSummarySerializer(many=True)
