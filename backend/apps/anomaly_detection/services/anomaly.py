from dataclasses import dataclass
from datetime import datetime, time, timedelta

import numpy as np
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from sklearn.ensemble import IsolationForest

from apps.audit.models import AuditLog
from apps.authentication.models import User

from ..models import AnomalyDetectionResult

FEATURE_SCHEMA_VERSION = "audit-profile-v1"
MODEL_VERSION = "isolation-forest-v1"
FEATURE_NAMES = ("total_events", "login_successes", "login_failures", "document_views", "document_downloads", "document_mutations", "denied_attempts", "unique_documents", "off_hours_events")
MINIMUM_PROFILES = 5
_model_cache = None


@dataclass
class AnalysisOutcome:
    status: str
    profiles: int
    results: list


def _events_for(user, start, end):
    # A run is itself audited. Exclude that operational event so repeated
    # analyses do not alter an administrator's behavioural profile.
    return AuditLog.objects.filter(
        user=user,
        timestamp__gte=start,
        timestamp__lt=end,
    ).exclude(resource_type="AnomalyDetection")


def build_features(user, start, end):
    events = list(_events_for(user, start, end))
    types = [event.event_type for event in events]
    local_tz = timezone.get_current_timezone()
    off_hours = sum(
        1
        for event in events
        if timezone.localtime(event.timestamp, local_tz).hour >= 22
        or timezone.localtime(event.timestamp, local_tz).hour < 6
    )
    document_ids = {event.resource_id for event in events if event.resource_type == "Document" and event.resource_id}
    return {
        "total_events": len(events),
        "login_successes": types.count(AuditLog.EventType.LOGIN_SUCCESS),
        "login_failures": types.count(AuditLog.EventType.LOGIN_FAILURE),
        "document_views": types.count(AuditLog.EventType.DOCUMENT_VIEW),
        "document_downloads": types.count(AuditLog.EventType.DOCUMENT_DOWNLOAD),
        "document_mutations": sum(types.count(value) for value in (AuditLog.EventType.DOCUMENT_CREATE, AuditLog.EventType.DOCUMENT_UPDATE, AuditLog.EventType.DOCUMENT_DELETE)),
        "denied_attempts": sum(types.count(value) for value in (AuditLog.EventType.UNAUTHORIZED_ACCESS, AuditLog.EventType.FORBIDDEN_ACTION)),
        "unique_documents": len(document_ids),
        "off_hours_events": off_hours,
    }


def _matrix(profiles):
    return np.array(
        [[profile[name] for name in FEATURE_NAMES] for profile in profiles],
        dtype=float,
    )


def analyze(window_days=7):
    global _model_cache
    if not isinstance(window_days, int) or not 1 <= window_days <= 90:
        raise ValueError("window_days must be an integer from 1 to 90.")
    local_now = timezone.localtime(timezone.now())
    end = timezone.make_aware(datetime.combine(local_now.date() + timedelta(days=1), time.min), timezone.get_current_timezone())
    start = end - timedelta(days=window_days)
    users = list(User.objects.filter(account_active=True).order_by("id"))
    profiles = [(user, build_features(user, start, end)) for user in users]
    # Zero activity remains meaningful but requires five active account profiles to train safely.
    if len(profiles) < MINIMUM_PROFILES:
        return AnalysisOutcome("insufficient_data", len(profiles), [])
    matrix = _matrix([profile for _, profile in profiles])
    model = IsolationForest(
        contamination=settings.ANOMALY_ISOLATION_FOREST_CONTAMINATION,
        random_state=settings.ANOMALY_ISOLATION_FOREST_RANDOM_STATE,
        n_estimators=100,
    )
    labels = model.fit_predict(matrix)
    scores = model.decision_function(matrix)  # lower values are more anomalous; negative means anomalous.
    _model_cache = model
    results = []
    # Persist the complete result set atomically; a failed write never leaves
    # a partially updated window that could be mistaken for a completed run.
    with transaction.atomic():
        for (user, profile), label, score in zip(profiles, labels, scores):
            classification = (
                AnomalyDetectionResult.Classification.ANOMALOUS
                if label == -1
                else AnomalyDetectionResult.Classification.NORMAL
            )
            result, _ = AnomalyDetectionResult.objects.update_or_create(
                subject_user=user,
                window_start=start,
                window_end=end,
                model_version=MODEL_VERSION,
                defaults={
                    "anomaly_score": float(score),
                    "classification": classification,
                    "feature_schema_version": FEATURE_SCHEMA_VERSION,
                    "feature_summary": profile,
                },
            )
            results.append(result)
    return AnalysisOutcome("trained", len(profiles), results)


def model_status():
    return {
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": FEATURE_NAMES,
        "minimum_profiles": MINIMUM_PROFILES,
        "loaded": _model_cache is not None,
    }
