import os
import uuid
from pathlib import PurePath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def private_document_upload_path(_instance, filename):
    """Store under a generated private name; never use the client filename as a path."""
    extension = PurePath(filename).suffix.lower()
    return f"documents/{uuid.uuid4().hex}{extension}"


class Document(models.Model):
    class Classification(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        INTERNAL = "INTERNAL", "Internal"
        CONFIDENTIAL = "CONFIDENTIAL", "Confidential"
        RESTRICTED = "RESTRICTED", "Restricted"

    class DocumentType(models.TextChoices):
        FIR = "FIR", "FIR"
        CHARGE_SHEET = "CHARGE_SHEET", "Charge Sheet"
        WITNESS_STATEMENT = "WITNESS_STATEMENT", "Witness Statement"
        FORENSIC_REPORT = "FORENSIC_REPORT", "Forensic Report"
        COURT_FILING = "COURT_FILING", "Court Filing"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=24, choices=DocumentType.choices)
    classification = models.CharField(max_length=16, choices=Classification.choices, default=Classification.INTERNAL)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_documents")
    file = models.FileField(upload_to=private_document_upload_path, max_length=500)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    content_type = models.CharField(max_length=127)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="updated_documents", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("owner", "is_active")), models.Index(fields=("classification", "is_active"))]

    def clean(self):
        if self.original_filename and ("/" in self.original_filename or "\\" in self.original_filename):
            raise ValidationError({"original_filename": "Filename must not contain path separators."})

    def __str__(self):
        return self.title
