from rest_framework import serializers

from .models import AnomalyDetectionResult


class AnomalyResultSerializer(serializers.ModelSerializer):
    subject = serializers.SerializerMethodField()

    class Meta:
        model = AnomalyDetectionResult
        fields = (
            "id",
            "subject",
            "window_start",
            "window_end",
            "anomaly_score",
            "classification",
            "model_version",
            "feature_schema_version",
            "feature_summary",
            "detected_at",
            "reviewed",
        )
        read_only_fields = fields

    def get_subject(self, obj):
        return {
            "id": obj.subject_user_id,
            "email": obj.subject_user.email,
            "name": obj.subject_user.name,
        }
