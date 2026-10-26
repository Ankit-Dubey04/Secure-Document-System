from django.urls import path
from .views import AnomalyDetailView, AnomalyListView, AnomalyRunView, AnomalyStatusView
urlpatterns = [path("status/", AnomalyStatusView.as_view(), name="anomaly-status"), path("run/", AnomalyRunView.as_view(), name="anomaly-run"), path("", AnomalyListView.as_view(), name="anomaly-list"), path("<int:pk>/", AnomalyDetailView.as_view(), name="anomaly-detail")]
