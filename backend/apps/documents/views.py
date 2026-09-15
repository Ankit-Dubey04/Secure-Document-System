from io import BytesIO

from django.http import FileResponse
from django.http import Http404
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.authentication.permissions import IsActiveUser
from apps.audit.models import AuditLog
from apps.audit.services.audit import record_event

from .models import Document
from .permissions import can_manage_document, readable_documents_for, require_document_create_permission
from .serializers import DocumentSerializer
from .services.crypto import DocumentDecryptionError, DocumentIntegrityError, EncryptionConfigurationError, decrypt_and_verify


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        return readable_documents_for(self.request.user).select_related("owner", "updated_by")

    def perform_create(self, serializer):
        require_document_create_permission(self.request.user)
        with transaction.atomic():
            document = serializer.save(owner=self.request.user, updated_by=self.request.user)
            record_event(AuditLog.EventType.DOCUMENT_CREATE, AuditLog.Outcome.SUCCESS, self.request.user, "Document", document.id, request=self.request)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        return readable_documents_for(self.request.user).select_related("owner", "updated_by")

    def get_object(self):
        try: return super().get_object()
        except Http404:
            record_event(AuditLog.EventType.UNAUTHORIZED_ACCESS, AuditLog.Outcome.DENIED, self.request.user, "Document", self.kwargs.get("pk", ""), request=self.request)
            raise

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        record_event(AuditLog.EventType.DOCUMENT_VIEW, AuditLog.Outcome.SUCCESS, request.user, "Document", kwargs["pk"], request=request)
        return response

    def perform_update(self, serializer):
        if not can_manage_document(self.request.user, self.get_object()):
            raise PermissionDenied("You cannot modify this document.")
        with transaction.atomic():
            document = serializer.save(updated_by=self.request.user)
            record_event(AuditLog.EventType.DOCUMENT_UPDATE, AuditLog.Outcome.SUCCESS, self.request.user, "Document", document.id, request=self.request)

    def perform_destroy(self, instance):
        if not can_manage_document(self.request.user, instance):
            raise PermissionDenied("You cannot delete this document.")
        with transaction.atomic():
            instance.is_active = False
            instance.updated_by = self.request.user
            instance.save(update_fields=("is_active", "updated_by", "updated_at"))
            record_event(AuditLog.EventType.DOCUMENT_DELETE, AuditLog.Outcome.SUCCESS, self.request.user, "Document", instance.id, request=self.request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentDownloadView(generics.RetrieveAPIView):
    """Authorization-bound download that decrypts and verifies before release."""

    permission_classes = [IsActiveUser]
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return readable_documents_for(self.request.user).select_related("owner", "updated_by")

    def get_object(self):
        try: return super().get_object()
        except Http404:
            record_event(AuditLog.EventType.UNAUTHORIZED_ACCESS, AuditLog.Outcome.DENIED, self.request.user, "Document", self.kwargs.get("pk", ""), request=self.request)
            raise

    def retrieve(self, request, *args, **kwargs):
        document = self.get_object()
        if not document.is_encrypted or not document.encryption_nonce or not document.plaintext_sha256:
            raise PermissionDenied("Document cannot be retrieved securely.")
        try:
            with document.file.open("rb") as encrypted_file:
                plaintext = decrypt_and_verify(encrypted_file.read(), document.encryption_nonce, document.plaintext_sha256)
        except (DocumentDecryptionError, DocumentIntegrityError, EncryptionConfigurationError) as exc:
            event_type = AuditLog.EventType.DOCUMENT_INTEGRITY_FAILURE if isinstance(exc, DocumentIntegrityError) else AuditLog.EventType.DOCUMENT_DECRYPTION_FAILURE
            record_event(event_type, AuditLog.Outcome.FAILURE, request.user, "Document", document.id, request=request)
            return Response({"detail": "Document cannot be retrieved securely."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        document.integrity_verified_at = timezone.now()
        document.save(update_fields=("integrity_verified_at", "updated_at"))
        record_event(AuditLog.EventType.DOCUMENT_DOWNLOAD, AuditLog.Outcome.SUCCESS, request.user, "Document", document.id, request=request)
        return FileResponse(BytesIO(plaintext), as_attachment=True, filename=document.original_filename, content_type=document.content_type)
