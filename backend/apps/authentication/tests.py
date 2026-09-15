from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User
from .permissions import CanAccessDocuments, CanManageDocuments, CanViewAuditLogs, CanViewSecurityInformation


class AuthenticationApiTests(APITestCase):
    password = "StrongPass123!"

    @classmethod
    def setUpTestData(cls):
        cls.employee = cls.create_user("employee@example.com", User.Role.EMPLOYEE)
        cls.manager = cls.create_user("manager@example.com", User.Role.MANAGER)
        cls.auditor = cls.create_user("auditor@example.com", User.Role.AUDITOR)
        cls.administrator = cls.create_user("admin@example.com", User.Role.ADMINISTRATOR)

    @classmethod
    def create_user(cls, email, role):
        return User.objects.create_user(email=email, name=email.split("@")[0], role=role, password=cls.password)

    def login(self, email="employee@example.com", password=None):
        return self.client.post(reverse("login"), {"email": email, "password": password or self.password}, format="json")

    def authenticate(self, user):
        token = self.login(user.email).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_successful_login_returns_access_and_refresh_without_password(self):
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertNotIn("password", response.data)

    def test_invalid_credentials_are_rejected(self):
        response = self.login(password="wrong-password")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("password", response.data)

    def test_inactive_account_cannot_log_in(self):
        self.employee.account_active = False
        self.employee.save(update_fields=["account_active"])
        response = self.login()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_identity_endpoint_rejects_anonymous_request(self):
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_jwt_returns_authenticated_user_profile_without_password(self):
        self.authenticate(self.employee)
        response = self.client.get(reverse("current-user"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.employee.email)
        self.assertEqual(response.data["role"], User.Role.EMPLOYEE)
        self.assertNotIn("password", response.data)

    def test_refresh_token_issues_new_access_token(self):
        login_response = self.login()
        response = self.client.post(reverse("token-refresh"), {"refresh": login_response.data["refresh"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertNotIn("password", response.data)

    def test_logout_blacklists_refresh_token(self):
        login_response = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        response = self.client.post(reverse("logout"), {"refresh": login_response.data["refresh"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        refresh_response = self.client.post(reverse("token-refresh"), {"refresh": login_response.data["refresh"]}, format="json")
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_administrator_can_access_user_administration(self):
        self.authenticate(self.administrator)
        response = self.client.get(reverse("user-administration-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_manager_employee_and_auditor_cannot_access_user_administration(self):
        for user in (self.manager, self.employee, self.auditor):
            with self.subTest(role=user.role):
                self.client.credentials()
                self.authenticate(user)
                response = self.client.get(reverse("user-administration-list"))
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_policy_matrix(self):
        expected = {
            User.Role.ADMINISTRATOR: (True, True, True, True),
            User.Role.MANAGER: (True, True, False, False),
            User.Role.EMPLOYEE: (True, False, False, False),
            User.Role.AUDITOR: (True, False, True, True),
        }
        policies = (CanAccessDocuments(), CanManageDocuments(), CanViewAuditLogs(), CanViewSecurityInformation())
        for user in (self.administrator, self.manager, self.employee, self.auditor):
            request = type("Request", (), {"user": user})()
            actual = tuple(policy.has_permission(request, None) for policy in policies)
            self.assertEqual(actual, expected[user.role])
