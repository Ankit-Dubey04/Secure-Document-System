from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from django.db import transaction

from .models import User
from .permissions import IsActiveUser, IsAdministrator
from .serializers import EmailTokenObtainPairSerializer, LogoutSerializer, UserProfileSerializer
from apps.audit.models import AuditLog
from apps.audit.services.audit import record_event


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer


class AuditedTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            record_event(AuditLog.EventType.TOKEN_REFRESH, AuditLog.Outcome.SUCCESS, request=request)
        return response


class LogoutView(APIView):
    """Blacklist the submitted refresh token, ending its ability to mint access tokens."""

    permission_classes = [IsActiveUser]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            record_event(AuditLog.EventType.LOGOUT, AuditLog.Outcome.SUCCESS, request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = [IsActiveUser]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class UserAdministrationListView(generics.ListAPIView):
    """Minimal Phase 2 user-administration read endpoint, administrator-only."""

    permission_classes = [IsAdministrator]
    serializer_class = UserProfileSerializer
    queryset = User.objects.order_by("email")
