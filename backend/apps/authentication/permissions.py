"""Reusable role-based permission classes for API views."""

from rest_framework.permissions import BasePermission

from .models import User


class IsActiveUser(BasePermission):
    """Requires a valid authenticated principal whose application account is active."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.account_active)


class RolePermission(BasePermission):
    """Base class for endpoint-level role policy; anonymous requests are denied."""

    allowed_roles = ()

    def has_permission(self, request, view):
        return IsActiveUser().has_permission(request, view) and (request.user.is_superuser or request.user.role in self.allowed_roles)


class IsAdministrator(RolePermission):
    allowed_roles = (User.Role.ADMINISTRATOR,)


class IsManagerOrAdministrator(RolePermission):
    allowed_roles = (User.Role.ADMINISTRATOR, User.Role.MANAGER)


class CanManageDocuments(IsManagerOrAdministrator):
    """Future document write operations: administrators and managers only."""


class CanAccessDocuments(RolePermission):
    """Future document read operations: all active business roles."""

    allowed_roles = tuple(User.Role.values)


class CanViewAuditLogs(RolePermission):
    """Future audit-log reads: administrators and auditors only."""

    allowed_roles = (User.Role.ADMINISTRATOR, User.Role.AUDITOR)


class CanViewSecurityInformation(CanViewAuditLogs):
    """Future security and anomaly views: administrators and auditors only."""
