from django.conf import settings
from django.db import models


class AnomalyDetectionResult(models.Model):
    class Classification(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        ANOMALOUS = "ANOMALOUS", "Anomalous"

    subject_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="anomaly_results")
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    anomaly_score = models.FloatField()
    classification = models.CharField(max_length=12, choices=Classification.choices)
    model_version = models.CharField(max_length=32)
    feature_schema_version = models.CharField(max_length=32)
    feature_summary = models.JSONField(default=dict)
    detected_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ("-detected_at",)
        constraints = [models.UniqueConstraint(fields=("subject_user", "window_start", "window_end", "model_version"), name="unique_anomaly_window_model")]
        indexes = [models.Index(fields=("classification", "detected_at"))]
