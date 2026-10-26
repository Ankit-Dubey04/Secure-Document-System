from django.test import TestCase
from django.urls import reverse


class UiShellTests(TestCase):
    def test_application_shell_serves_ui_assets_and_no_secrets(self):
        response = self.client.get(reverse("application-shell"))
        self.assertContains(response, "SecureDocs")
        self.assertContains(response, "ui/app.js")
        self.assertNotContains(response, "DOCUMENT_ENCRYPTION_KEY")
