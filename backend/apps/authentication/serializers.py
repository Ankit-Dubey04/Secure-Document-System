from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "department", "clearance_level", "account_active", "created_at", "updated_at")
        read_only_fields = fields


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Authenticates the project's email-based user model and returns a token pair."""

    username_field = User.EMAIL_FIELD

    def validate(self, attrs):
        email = attrs.get(self.username_field)
        password = attrs.get("password")
        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user or not user.account_active:
            raise AuthenticationFailed("No active account found with the given credentials.")
        self.user = user
        return super().validate(attrs)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value):
        from rest_framework_simplejwt.tokens import RefreshToken
        try:
            RefreshToken(value)
        except Exception as exc:
            raise serializers.ValidationError("Invalid or expired refresh token.") from exc
        return value
