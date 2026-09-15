from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.authentication.permissions import CanViewAuditLogs
from .services.audit import record_event
from .models import AuditLog
from .models import AuditLog
from .serializers import AuditLogSerializer
from .services.audit import verify_chain
class CanViewAuditLogsWithEvent(CanViewAuditLogs):
    def has_permission(self, request, view):
        allowed = super().has_permission(request, view)
        if not allowed and getattr(request.user, "is_authenticated", False):
            record_event(AuditLog.EventType.FORBIDDEN_ACTION, AuditLog.Outcome.DENIED, request.user, "Audit", request.path, request=request)
        return allowed

class AuditListView(generics.ListAPIView):
    permission_classes = [CanViewAuditLogsWithEvent]; serializer_class = AuditLogSerializer
    def get_queryset(self):
        qs = AuditLog.objects.all().select_related("user")
        for field in ("event_type","outcome","resource_type","resource_id","user"):
            if self.request.query_params.get(field): qs = qs.filter(**{field: self.request.query_params[field]})
        return qs
class AuditVerifyView(APIView):
    permission_classes = [CanViewAuditLogsWithEvent]
    def get(self, request): return Response(verify_chain())
