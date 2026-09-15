from django.urls import path
from .views import AuditedTokenRefreshView, CurrentUserView, LoginView, LogoutView, UserAdministrationListView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", AuditedTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("users/", UserAdministrationListView.as_view(), name="user-administration-list"),
]
