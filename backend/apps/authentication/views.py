from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .permissions import IsActiveUser, IsAdministrator
from .serializers import EmailTokenObtainPairSerializer, LogoutSerializer, UserProfileSerializer


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmailTokenObtainPairSerializer


class LogoutView(APIView):
    """Blacklist the submitted refresh token, ending its ability to mint access tokens."""

    permission_classes = [IsActiveUser]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = RefreshToken(serializer.validated_data["refresh"])
        token.blacklist()
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
