from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from apps.audit.models import AuditLog
from apps.audit.services.audit import record_event


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
            record_event(AuditLog.EventType.LOGIN_FAILURE, AuditLog.Outcome.FAILURE, metadata={"attempted_email": email}, request=self.context.get("request"))
            raise AuthenticationFailed("No active account found with the given credentials.")
        self.user = user
        data = super().validate(attrs)
        record_event(AuditLog.EventType.LOGIN_SUCCESS, AuditLog.Outcome.SUCCESS, user, request=self.context.get("request"))
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate_refresh(self, value):
        from rest_framework_simplejwt.tokens import RefreshToken
        try:
            RefreshToken(value)
        except Exception as exc:
            raise serializers.ValidationError("Invalid or expired refresh token.") from exc
        return value
