import uuid
from django.utils import timezone

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class EventType(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS"; LOGIN_FAILURE = "LOGIN_FAILURE"; LOGOUT = "LOGOUT"; TOKEN_REFRESH = "TOKEN_REFRESH"
        DOCUMENT_CREATE = "DOCUMENT_CREATE"; DOCUMENT_VIEW = "DOCUMENT_VIEW"; DOCUMENT_DOWNLOAD = "DOCUMENT_DOWNLOAD"; DOCUMENT_UPDATE = "DOCUMENT_UPDATE"; DOCUMENT_DELETE = "DOCUMENT_DELETE"
        DOCUMENT_INTEGRITY_FAILURE = "DOCUMENT_INTEGRITY_FAILURE"; DOCUMENT_DECRYPTION_FAILURE = "DOCUMENT_DECRYPTION_FAILURE"
        UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"; FORBIDDEN_ACTION = "FORBIDDEN_ACTION"; SECURITY_EVENT = "SECURITY_EVENT"; SYSTEM_EVENT = "SYSTEM_EVENT"
    class Outcome(models.TextChoices): SUCCESS = "SUCCESS"; FAILURE = "FAILURE"; DENIED = "DENIED"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, editable=False, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    event_type = models.CharField(max_length=32, choices=EventType.choices, db_index=True)
    outcome = models.CharField(max_length=8, choices=Outcome.choices, db_index=True)
    resource_type = models.CharField(max_length=64, blank=True)
    resource_id = models.CharField(max_length=128, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    previous_hash = models.CharField(max_length=64, default="GENESIS")
    current_hash = models.CharField(max_length=64, unique=True)
    class Meta:
        ordering = ("timestamp", "id")
        indexes = [models.Index(fields=("event_type", "outcome")), models.Index(fields=("resource_type", "resource_id"))]


class AuditChainState(models.Model):
    """Single locked row that serializes app-generated audit-chain appends."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    last_hash = models.CharField(max_length=64, default="GENESIS")
