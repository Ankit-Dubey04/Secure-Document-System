import base64
import os

from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.authentication.models import User
from apps.documents.models import Document
from .models import AuditChainState, AuditLog
from .services.audit import record_event, verify_chain

TEST_ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")

@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}, DOCUMENT_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class AuditTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(email="admin-audit@example.com", name="Admin", role=User.Role.ADMINISTRATOR, clearance_level=User.ClearanceLevel.RESTRICTED, password="StrongPass123!")
        cls.auditor = User.objects.create_user(email="auditor-audit@example.com", name="Auditor", role=User.Role.AUDITOR, password="StrongPass123!")
        cls.employee = User.objects.create_user(email="employee-audit@example.com", name="Employee", role=User.Role.EMPLOYEE, password="StrongPass123!")
    def auth(self, user): self.client.force_authenticate(user)
    def test_chain_links_and_detects_tampering(self):
        first = record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin, metadata={"x": 1})
        second = record_event(AuditLog.EventType.SECURITY_EVENT, AuditLog.Outcome.FAILURE, self.admin)
        self.assertEqual(second.previous_hash, first.current_hash); self.assertTrue(verify_chain()["valid"])
        AuditLog.objects.filter(pk=first.pk).update(metadata={"x": 2})
        self.assertFalse(verify_chain()["valid"])

    def test_hash_and_link_tampering_cases_are_detected(self):
        first = record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin)
        second = record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin)
        for field, value in (("current_hash", "0" * 64), ("previous_hash", "0" * 64)):
            with self.subTest(field=field):
                AuditLog.objects.filter(pk=second.pk).update(**{field: value})
                self.assertFalse(verify_chain()["valid"])
                AuditLog.objects.filter(pk=second.pk).update(**{field: getattr(second, field)})
        AuditChainState.objects.filter(pk=1).update(last_hash="0" * 64)
        self.assertEqual(verify_chain()["reason"], "chain_state_mismatch")

    def test_genesis_and_interrupted_chain_are_detected(self):
        first = record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin)
        second = record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin)
        AuditLog.objects.filter(pk=first.pk).update(previous_hash="broken-genesis")
        self.assertEqual(verify_chain()["reason"], "previous_hash_mismatch")
        AuditLog.objects.filter(pk=first.pk).update(previous_hash="GENESIS")
        AuditLog.objects.filter(pk=first.pk).delete()
        self.assertEqual(verify_chain()["reason"], "previous_hash_mismatch")

    def test_sensitive_metadata_is_recursively_removed(self):
        event = record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin, metadata={"safe": "yes", "password": "x", "nested": [{"token": "x", "keep": 1}], "api_key": "x"})
        self.assertEqual(event.metadata, {"safe": "yes", "nested": [{"keep": 1}]})
    def test_audit_api_is_role_restricted_and_read_only(self):
        record_event(AuditLog.EventType.SYSTEM_EVENT, AuditLog.Outcome.SUCCESS, self.admin)
        self.assertEqual(self.client.get(reverse("audit-list")).status_code, status.HTTP_401_UNAUTHORIZED)
        self.auth(self.employee); self.assertEqual(self.client.get(reverse("audit-list")).status_code, status.HTTP_403_FORBIDDEN)
        self.auth(self.auditor); self.assertEqual(self.client.get(reverse("audit-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(reverse("audit-list"), {}).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(self.client.get(reverse("audit-verify")).data["valid"])

    def test_admin_is_read_only_for_audit_models(self):
        request = RequestFactory().get("/admin/"); request.user = self.admin
        audit_admin = admin.site._registry[AuditLog]
        state_admin = admin.site._registry[AuditChainState]
        self.assertFalse(audit_admin.has_add_permission(request)); self.assertFalse(audit_admin.has_change_permission(request)); self.assertFalse(audit_admin.has_delete_permission(request))
        self.assertFalse(state_admin.has_add_permission(request)); self.assertFalse(state_admin.has_change_permission(request)); self.assertFalse(state_admin.has_delete_permission(request))

    def test_authentication_actions_create_sanitized_events(self):
        login = self.client.post(reverse("login"), {"email": self.admin.email, "password": "StrongPass123!"}, format="json")
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.LOGIN_SUCCESS, user=self.admin).exists())
        failed = self.client.post(reverse("login"), {"email": "nobody@example.com", "password": "not-recorded"}, format="json")
        self.assertEqual(failed.status_code, status.HTTP_401_UNAUTHORIZED)
        failure = AuditLog.objects.filter(event_type=AuditLog.EventType.LOGIN_FAILURE).latest("timestamp")
        self.assertNotIn("password", failure.metadata); self.assertNotIn("not-recorded", str(failure.metadata))
        refresh = self.client.post(reverse("token-refresh"), {"refresh": login.data["refresh"]}, format="json")
        self.assertEqual(refresh.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.TOKEN_REFRESH).exists())
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assertEqual(self.client.post(reverse("logout"), {"refresh": refresh.data["refresh"]}, format="json").status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.LOGOUT, user=self.admin).exists())

    def test_document_events_and_denied_access_are_recorded(self):
        self.client.force_authenticate(self.employee)
        data = {"title": "Evidence", "document_type": "OTHER", "classification": "INTERNAL", "file": SimpleUploadedFile("evidence.pdf", b"plaintext", content_type="application/pdf")}
        create = self.client.post(reverse("document-list"), data, format="multipart")
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        document_id = create.data["id"]
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.DOCUMENT_CREATE).exists())
        self.assertEqual(self.client.get(reverse("document-detail", args=[document_id])).status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.DOCUMENT_VIEW).exists())
        self.assertEqual(self.client.patch(reverse("document-detail", args=[document_id]), {"title": "Updated"}, format="json").status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.DOCUMENT_UPDATE).exists())
        download = self.client.get(reverse("document-download", args=[document_id]))
        self.assertEqual(download.status_code, status.HTTP_200_OK); self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.DOCUMENT_DOWNLOAD).exists())
        self.assertEqual(self.client.delete(reverse("document-detail", args=[document_id])).status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.DOCUMENT_DELETE).exists())

    def test_denied_document_metadata_and_download_are_audited(self):
        self.client.force_authenticate(self.employee)
        create = self.client.post(reverse("document-list"), {"title": "Private", "document_type": "OTHER", "classification": "INTERNAL", "file": SimpleUploadedFile("private.pdf", b"private", content_type="application/pdf")}, format="multipart")
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.auditor)
        # Auditors may read Internal documents, so use a Restricted document created by admin.
        self.client.force_authenticate(self.admin)
        restricted = self.client.post(reverse("document-list"), {"title": "Restricted", "document_type": "OTHER", "classification": "RESTRICTED", "file": SimpleUploadedFile("restricted.pdf", b"private", content_type="application/pdf")}, format="multipart")
        self.client.force_authenticate(self.employee)
        for endpoint in ("document-detail", "document-download"):
            response = self.client.get(reverse(endpoint, args=[restricted.data["id"]]))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertGreaterEqual(AuditLog.objects.filter(event_type=AuditLog.EventType.UNAUTHORIZED_ACCESS, outcome=AuditLog.Outcome.DENIED, user=self.employee).count(), 2)

    def test_tampered_encrypted_document_records_failure_without_plaintext(self):
        self.client.force_authenticate(self.employee)
        create = self.client.post(reverse("document-list"), {"title": "Tamper", "document_type": "OTHER", "classification": "INTERNAL", "file": SimpleUploadedFile("tamper.pdf", b"protected text", content_type="application/pdf")}, format="multipart")
        document = Document.objects.get(pk=create.data["id"])
        document.file.save(document.file.name, SimpleUploadedFile("corrupt.bin", b"corrupted"), save=True)
        response = self.client.get(reverse("document-download", args=[document.id]))
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertNotIn(b"protected text", response.content)
        self.assertTrue(AuditLog.objects.filter(event_type=AuditLog.EventType.DOCUMENT_DECRYPTION_FAILURE, outcome=AuditLog.Outcome.FAILURE, resource_id=str(document.id)).exists())
