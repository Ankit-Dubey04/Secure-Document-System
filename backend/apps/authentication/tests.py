from django.test import TestCase
from .models import User

class UserModelTests(TestCase):
    def test_user_uses_email_and_hashes_password(self):
        user = User.objects.create_user(email="employee@example.com", name="Employee", password="SafePass123!")
        self.assertEqual(user.email, "employee@example.com")
        self.assertTrue(user.check_password("SafePass123!"))
        self.assertNotEqual(user.password, "SafePass123!")
