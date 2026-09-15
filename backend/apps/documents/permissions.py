"""Document RBAC and object-level policy helpers."""

from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from apps.authentication.models import User
from apps.authentication.permissions import IsActiveUser

from .models import Document


def readable_documents_for(user):
    queryset = Document.objects.filter(is_active=True)
    if user.is_superuser or user.role == User.Role.ADMINISTRATOR:
        return queryset
    if user.role == User.Role.MANAGER:
        return queryset.filter(Q(owner=user) | Q(owner__department=user.department, owner__department__gt=""))
    if user.role == User.Role.EMPLOYEE:
        return queryset.filter(Q(owner=user) | Q(classification=Document.Classification.PUBLIC))
    if user.role == User.Role.AUDITOR:
        return queryset.filter(Q(owner=user) | Q(classification__in=(Document.Classification.PUBLIC, Document.Classification.INTERNAL, Document.Classification.CONFIDENTIAL)))
    return queryset.none()


def can_create_document(user):
    return user.is_superuser or user.role in (User.Role.ADMINISTRATOR, User.Role.MANAGER, User.Role.EMPLOYEE)


def can_manage_document(user, document):
    if user.is_superuser or user.role == User.Role.ADMINISTRATOR:
        return True
    if user.role == User.Role.MANAGER:
        return bool(document.owner.department and document.owner.department == user.department)
    return user.role == User.Role.EMPLOYEE and document.owner_id == user.id


class CanAccessDocument(IsActiveUser):
    def has_object_permission(self, request, view, obj):
        return readable_documents_for(request.user).filter(pk=obj.pk).exists()


class CanManageDocument(IsActiveUser):
    def has_object_permission(self, request, view, obj):
        return can_manage_document(request.user, obj)


def require_document_create_permission(user):
    if not can_create_document(user):
        raise PermissionDenied("Your role cannot create documents.")
