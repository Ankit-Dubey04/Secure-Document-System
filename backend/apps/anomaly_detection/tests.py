from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditLog
from apps.audit.services.audit import record_event
from apps.authentication.models import User

from .models import AnomalyDetectionResult
from .services.anomaly import FEATURE_NAMES, analyze, build_features, model_status


class AnomalyDetectionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = cls.user("admin-ml@example.com", User.Role.ADMINISTRATOR)
        cls.auditor = cls.user("auditor-ml@example.com", User.Role.AUDITOR)
        cls.employee = cls.user("employee-ml@example.com", User.Role.EMPLOYEE)
        cls.subjects = [cls.user(f"subject{i}@example.com", User.Role.EMPLOYEE) for i in range(5)]

    @classmethod
    def user(cls, email, role):
        return User.objects.create_user(email=email, name=email.split("@")[0], role=role, password="StrongPass123!")

    def seed_profiles(self):
        for user in self.subjects[:4]:
            record_event(AuditLog.EventType.LOGIN_SUCCESS, AuditLog.Outcome.SUCCESS, user)
            record_event(AuditLog.EventType.DOCUMENT_VIEW, AuditLog.Outcome.SUCCESS, user, "Document", f"doc-{user.id}")
        for _ in range(20):
            record_event(AuditLog.EventType.UNAUTHORIZED_ACCESS, AuditLog.Outcome.DENIED, self.subjects[4], "Document", "target")
        record_event(AuditLog.EventType.LOGIN_FAILURE, AuditLog.Outcome.FAILURE, self.subjects[4])

    def test_empty_and_insufficient_data_return_explicit_status(self):
        User.objects.update(account_active=False)
        empty = analyze(7)
        self.assertEqual(empty.status, "insufficient_data")
        self.assertEqual(empty.profiles, 0)
        User.objects.filter(pk__in=[self.admin.pk, self.auditor.pk]).update(account_active=True)
        outcome = analyze(7)
        self.assertEqual(outcome.status, "insufficient_data")
        self.assertEqual(outcome.profiles, 2)
        self.assertEqual(outcome.results, [])
        self.assertEqual(list(model_status()["feature_names"]), list(FEATURE_NAMES))

    def test_features_use_actual_audit_event_fields(self):
        user = self.subjects[0]
        record_event(AuditLog.EventType.LOGIN_SUCCESS, AuditLog.Outcome.SUCCESS, user)
        record_event(AuditLog.EventType.DOCUMENT_DOWNLOAD, AuditLog.Outcome.SUCCESS, user, "Document", "x")
        record_event(AuditLog.EventType.UNAUTHORIZED_ACCESS, AuditLog.Outcome.DENIED, user)
        features = build_features(user, timezone.now() - timedelta(days=1), timezone.now() + timedelta(days=1))
        self.assertEqual(features["login_successes"], 1)
        self.assertEqual(features["document_downloads"], 1)
        self.assertEqual(features["denied_attempts"], 1)
        self.assertEqual(features["unique_documents"], 1)

    def test_synthetic_anomaly_is_reproducible_and_persists_idempotently(self):
        self.seed_profiles()
        first = analyze(7)
        initial = {
            result.subject_user_id: (result.classification, result.anomaly_score)
            for result in first.results
        }
        second = analyze(7)
        self.assertEqual(first.status, "trained")
        self.assertEqual(AnomalyDetectionResult.objects.count(), len(first.results))
        self.assertEqual(AnomalyDetectionResult.objects.count(), len(second.results))
        unusual = AnomalyDetectionResult.objects.get(subject_user=self.subjects[4])
        self.assertEqual(
            unusual.classification,
            AnomalyDetectionResult.Classification.ANOMALOUS,
        )
        self.assertLess(unusual.anomaly_score, 0)
        repeated = {
            result.subject_user_id: (result.classification, result.anomaly_score)
            for result in second.results
        }
        self.assertEqual(initial, repeated)

    def test_api_requires_security_roles_and_returns_safe_results(self):
        self.seed_profiles()
        self.assertEqual(
            self.client.get(reverse("anomaly-status")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.client.force_authenticate(self.employee)
        self.assertEqual(
            self.client.post(
                reverse("anomaly-run"), {"window_days": 7}, format="json"
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("anomaly-run"), {"window_days": 7}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.admin,
                event_type=AuditLog.EventType.SYSTEM_EVENT,
                resource_type="AnomalyDetection",
            ).exists()
        )
        list_response = self.client.get(reverse("anomaly-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        result = list_response.data[0]
        self.assertEqual(set(result["feature_summary"]), set(FEATURE_NAMES))
        self.assertNotIn("metadata", result)
        self.assertNotIn("password", result)
        self.assertNotIn("token", result)
        self.client.force_authenticate(self.auditor)
        self.assertEqual(
            self.client.get(reverse("anomaly-status")).status_code,
            status.HTTP_200_OK,
        )

    def test_api_rejects_invalid_window(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.post(
                reverse("anomaly-run"), {"window_days": 0}, format="json"
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(
                reverse("anomaly-run"), {"window_days": "nope"}, format="json"
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
