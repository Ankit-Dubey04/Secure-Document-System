from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import CanViewSecurityInformation
from apps.audit.models import AuditLog
from apps.audit.services.audit import record_event

from .models import AnomalyDetectionResult
from .serializers import AnomalyResultSerializer
from .services.anomaly import analyze, model_status


class AnomalyStatusView(APIView):
    permission_classes = [CanViewSecurityInformation]

    def get(self, request):
        return Response(model_status())

class AnomalyRunView(APIView):
    permission_classes = [CanViewSecurityInformation]

    def post(self, request):
        days = request.data.get("window_days", 7)
        try:
            days = int(days)
            outcome = analyze(days)
        except (TypeError, ValueError) as exc:
            raise ValidationError({"window_days": str(exc)})
        record_event(
            AuditLog.EventType.SYSTEM_EVENT,
            AuditLog.Outcome.SUCCESS,
            request.user,
            "AnomalyDetection",
            metadata={"status": outcome.status, "profiles": outcome.profiles},
            request=request,
        )
        return Response(
            {
                "status": outcome.status,
                "profiles": outcome.profiles,
                "results_created": len(outcome.results),
            },
            status=status.HTTP_200_OK,
        )

class AnomalyListView(generics.ListAPIView):
    permission_classes = [CanViewSecurityInformation]
    serializer_class = AnomalyResultSerializer
    queryset = AnomalyDetectionResult.objects.select_related("subject_user").all()[:200]

class AnomalyDetailView(generics.RetrieveAPIView):
    permission_classes = [CanViewSecurityInformation]
    serializer_class = AnomalyResultSerializer
    queryset = AnomalyDetectionResult.objects.select_related("subject_user")
