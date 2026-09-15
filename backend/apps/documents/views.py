from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.authentication.permissions import IsActiveUser

from .models import Document
from .permissions import can_manage_document, readable_documents_for, require_document_create_permission
from .serializers import DocumentSerializer


class DocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        return readable_documents_for(self.request.user).select_related("owner", "updated_by")

    def perform_create(self, serializer):
        require_document_create_permission(self.request.user)
        serializer.save(owner=self.request.user, updated_by=self.request.user)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsActiveUser]

    def get_queryset(self):
        return readable_documents_for(self.request.user).select_related("owner", "updated_by")

    def perform_update(self, serializer):
        if not can_manage_document(self.request.user, self.get_object()):
            raise PermissionDenied("You cannot modify this document.")
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if not can_manage_document(self.request.user, instance):
            raise PermissionDenied("You cannot delete this document.")
        instance.is_active = False
        instance.updated_by = self.request.user
        instance.save(update_fields=("is_active", "updated_by", "updated_at"))
        return Response(status=status.HTTP_204_NO_CONTENT)
