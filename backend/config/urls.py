"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from .ui_views import application_shell

def api_health(_request):
    return JsonResponse({"status": "ok", "service": "secure-document-management-api"})

urlpatterns = [
    path("", application_shell, name="application-shell"),
    path('admin/', admin.site.urls),
    path("api/health/", api_health, name="api-health"),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/documents/", include("apps.documents.urls")),
    path("api/audit/", include("apps.audit.urls")),
    path("api/anomalies/", include("apps.anomaly_detection.urls")),
]
