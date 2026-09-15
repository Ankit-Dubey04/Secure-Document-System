import base64
import hashlib
import os

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import User

from .models import Document
from .services.crypto import DocumentDecryptionError, DocumentIntegrityError, EncryptionConfigurationError, decrypt_and_verify, encrypt_plaintext


TEST_ENCRYPTION_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode("ascii")


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}}, DOCUMENT_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class DocumentApiTests(APITestCase):
    password = "StrongPass123!"

    @classmethod
    def setUpTestData(cls):
        cls.employee = cls.make_user("employee@example.com", User.Role.EMPLOYEE, "Investigations")
        cls.other_employee = cls.make_user("other@example.com", User.Role.EMPLOYEE, "Legal")
        cls.manager = cls.make_user("manager@example.com", User.Role.MANAGER, "Investigations", User.ClearanceLevel.RESTRICTED)
        cls.auditor = cls.make_user("auditor@example.com", User.Role.AUDITOR, "Audit", User.ClearanceLevel.CONFIDENTIAL)
        cls.admin = cls.make_user("admin@example.com", User.Role.ADMINISTRATOR, "Administration", User.ClearanceLevel.RESTRICTED)

    @classmethod
    def make_user(cls, email, role, department, clearance=User.ClearanceLevel.INTERNAL):
        return User.objects.create_user(email=email, name=email.split("@")[0], role=role, department=department, clearance_level=clearance, password=cls.password)

    def authenticate(self, user):
        login = self.client.post(reverse("login"), {"email": user.email, "password": self.password}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    @staticmethod
    def upload(name="report.pdf", content=b"document", content_type="application/pdf"):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def payload(self, **overrides):
        data = {"title": "Case report", "description": "Evidence summary", "document_type": Document.DocumentType.FORENSIC_REPORT, "classification": Document.Classification.INTERNAL, "file": self.upload()}
        data.update(overrides)
        return data

    def create_document(self, owner, **overrides):
        file = overrides.pop("file", self.upload())
        encrypted = encrypt_plaintext(file.read())
        return Document.objects.create(title=overrides.pop("title", "Stored document"), description="", document_type=overrides.pop("document_type", Document.DocumentType.OTHER), classification=overrides.pop("classification", Document.Classification.INTERNAL), owner=owner, updated_by=owner, file=SimpleUploadedFile(file.name, encrypted.ciphertext, content_type="application/octet-stream"), original_filename=file.name, file_size=file.size, content_type=file.content_type, plaintext_sha256=encrypted.plaintext_sha256, encryption_nonce=encrypted.nonce, is_encrypted=True, **overrides)

    def test_model_records_owner_metadata_and_timestamps(self):
        document = self.create_document(self.employee)
        self.assertEqual(document.owner, self.employee)
        self.assertEqual(document.original_filename, "report.pdf")
        self.assertGreater(document.file_size, 0)
        self.assertIsNotNone(document.created_at)
        self.assertIsNotNone(document.updated_at)

    def test_model_rejects_unsupported_choice_during_validation(self):
        document = self.create_document(self.employee, classification="SECRET")
        with self.assertRaises(ValidationError):
            document.full_clean()

    def test_unauthenticated_document_request_is_rejected(self):
        response = self.client.get(reverse("document-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_valid_upload_assigns_server_side_owner_and_hides_storage_path(self):
        self.authenticate(self.employee)
        response = self.client.post(reverse("document-list"), self.payload(owner=str(self.admin.id)), format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        document = Document.objects.get(pk=response.data["id"])
        self.assertEqual(document.owner, self.employee)
        self.assertNotIn("file", response.data)
        self.assertNotIn("private_media", str(response.data))
        with document.file.open("rb") as encrypted_file:
            self.assertNotEqual(encrypted_file.read(), b"document")
        self.assertTrue(document.is_encrypted)
        self.assertEqual(document.plaintext_sha256, hashlib.sha256(b"document").hexdigest())

    def test_rejects_missing_empty_unsupported_or_mismatched_upload(self):
        self.authenticate(self.employee)
        missing_file_payload = self.payload()
        missing_file_payload.pop("file")
        self.assertEqual(self.client.post(reverse("document-list"), missing_file_payload, format="multipart").status_code, status.HTTP_400_BAD_REQUEST)
        cases = (
            self.payload(file=self.upload(content=b"")),
            self.payload(file=self.upload("script.exe", content_type="application/octet-stream")),
            self.payload(file=self.upload("report.pdf", content_type="text/plain")),
        )
        for payload in cases:
            with self.subTest(payload=payload.get("file")):
                response = self.client.post(reverse("document-list"), payload, format="multipart")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_oversized_and_safely_normalizes_client_filename(self):
        self.authenticate(self.employee)
        oversized = self.upload(content=b"x" * (10 * 1024 * 1024 + 1))
        response = self.client.post(reverse("document-list"), self.payload(file=oversized), format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(reverse("document-list"), self.payload(file=self.upload("..\\secret.pdf")), format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.get(pk=response.data["id"]).original_filename, "secret.pdf")

    def test_safe_generated_paths_prevent_filename_collisions(self):
        self.authenticate(self.employee)
        first = self.client.post(reverse("document-list"), self.payload(file=self.upload("same.pdf")), format="multipart")
        second = self.client.post(reverse("document-list"), self.payload(file=self.upload("same.pdf")), format="multipart")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        paths = list(Document.objects.filter(owner=self.employee).values_list("file", flat=True))
        self.assertEqual(len(paths), 2)
        self.assertNotEqual(paths[0], paths[1])

    def test_employee_listing_and_object_access_do_not_leak_other_internal_document(self):
        own = self.create_document(self.employee)
        other_internal = self.create_document(self.other_employee, classification=Document.Classification.INTERNAL)
        public = self.create_document(self.other_employee, classification=Document.Classification.PUBLIC)
        self.authenticate(self.employee)
        response = self.client.get(reverse("document-list"))
        ids = {item["id"] for item in response.data}
        self.assertEqual(ids, {str(own.id), str(public.id)})
        detail = self.client.get(reverse("document-detail", args=[other_internal.id]))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_manager_can_manage_department_document_but_not_other_department(self):
        department_document = self.create_document(self.employee)
        other_document = self.create_document(self.other_employee)
        self.authenticate(self.manager)
        allowed = self.client.patch(reverse("document-detail", args=[department_document.id]), {"title": "Manager updated"}, format="json")
        denied = self.client.patch(reverse("document-detail", args=[other_document.id]), {"title": "Forbidden"}, format="json")
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

    def test_auditor_can_read_confidential_but_cannot_create_or_read_restricted(self):
        confidential = self.create_document(self.other_employee, classification=Document.Classification.CONFIDENTIAL)
        restricted = self.create_document(self.manager, classification=Document.Classification.RESTRICTED)
        self.authenticate(self.auditor)
        self.assertEqual(self.client.get(reverse("document-detail", args=[confidential.id])).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("document-detail", args=[restricted.id])).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post(reverse("document-list"), self.payload(), format="multipart").status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_modify_or_delete_another_visible_public_document(self):
        public = self.create_document(self.other_employee, classification=Document.Classification.PUBLIC)
        self.authenticate(self.employee)
        self.assertEqual(self.client.patch(reverse("document-detail", args=[public.id]), {"title": "No"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(reverse("document-detail", args=[public.id])).status_code, status.HTTP_403_FORBIDDEN)

    def test_administrator_can_manage_and_soft_delete_any_document(self):
        document = self.create_document(self.other_employee)
        self.authenticate(self.admin)
        self.assertEqual(self.client.patch(reverse("document-detail", args=[document.id]), {"classification": Document.Classification.RESTRICTED}, format="json").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(reverse("document-detail", args=[document.id])).status_code, status.HTTP_204_NO_CONTENT)
        document.refresh_from_db()
        self.assertFalse(document.is_active)

    def test_authorized_download_decrypts_and_verifies_plaintext(self):
        document = self.create_document(self.employee, file=self.upload(content=b"verified plaintext"))
        self.authenticate(self.employee)
        response = self.client.get(reverse("document-download", args=[document.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(response.streaming_content), b"verified plaintext")
        document.refresh_from_db()
        self.assertIsNotNone(document.integrity_verified_at)

    def test_tampered_ciphertext_never_returns_plaintext(self):
        document = self.create_document(self.employee, file=self.upload(content=b"do not release"))
        document.file.save(document.file.name, SimpleUploadedFile("tampered.bin", b"tampered"), save=True)
        self.authenticate(self.employee)
        response = self.client.get(reverse("document-download", args=[document.id]))
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertNotIn(b"do not release", response.content)

    def test_unauthorized_user_cannot_download_hidden_document(self):
        document = self.create_document(self.other_employee, classification=Document.Classification.INTERNAL)
        self.authenticate(self.employee)
        self.assertEqual(self.client.get(reverse("document-download", args=[document.id])).status_code, status.HTTP_404_NOT_FOUND)


@override_settings(DOCUMENT_ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class CryptoServiceTests(APITestCase):
    @override_settings(DOCUMENT_ENCRYPTION_KEY=None)
    def test_missing_key_is_rejected_safely(self):
        with self.assertRaises(EncryptionConfigurationError):
            encrypt_plaintext(b"plaintext")

    @override_settings(DOCUMENT_ENCRYPTION_KEY="not-a-valid-aes-key")
    def test_invalid_key_is_rejected_safely(self):
        with self.assertRaises(EncryptionConfigurationError):
            encrypt_plaintext(b"plaintext")

    def test_encryptions_use_unique_nonce_and_decrypt_with_correct_key(self):
        first = encrypt_plaintext(b"same plaintext")
        second = encrypt_plaintext(b"same plaintext")
        self.assertNotEqual(first.nonce, second.nonce)
        self.assertNotEqual(first.ciphertext, second.ciphertext)
        self.assertEqual(decrypt_and_verify(first.ciphertext, first.nonce, first.plaintext_sha256), b"same plaintext")

    def test_corruption_wrong_nonce_and_hash_mismatch_are_rejected(self):
        encrypted = encrypt_plaintext(b"protected")
        with self.assertRaises(DocumentDecryptionError):
            decrypt_and_verify(encrypted.ciphertext[:-1] + b"x", encrypted.nonce, encrypted.plaintext_sha256)
        with self.assertRaises(DocumentDecryptionError):
            decrypt_and_verify(encrypted.ciphertext, b"0" * 12, encrypted.plaintext_sha256)
        with self.assertRaises(DocumentIntegrityError):
            decrypt_and_verify(encrypted.ciphertext, encrypted.nonce, "0" * 64)
import base64
import os
