from django.contrib import admin

from .models import AnomalyDetectionResult


@admin.register(AnomalyDetectionResult)
class AnomalyDetectionResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "subject_user",
        "classification",
        "anomaly_score",
        "window_start",
        "window_end",
        "detected_at",
        "reviewed",
    )
    list_filter = ("classification", "reviewed", "model_version")
    search_fields = ("subject_user__email",)
    readonly_fields = (
        "subject_user",
        "window_start",
        "window_end",
        "anomaly_score",
        "classification",
        "model_version",
        "feature_schema_version",
        "feature_summary",
        "detected_at",
    )
