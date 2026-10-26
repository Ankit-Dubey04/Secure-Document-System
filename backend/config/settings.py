"""Django configuration for the secure document management backend."""
import os
from datetime import timedelta
from pathlib import Path
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

def load_local_env():
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists(): return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

load_local_env()
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")
    SECRET_KEY = get_random_secret_key()
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions",
    "django.contrib.messages", "django.contrib.staticfiles", "rest_framework", "rest_framework_simplejwt.token_blacklist", "apps.authentication",
    "apps.documents", "apps.audit", "apps.security", "apps.anomaly_detection",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": os.environ.get("DATABASE_NAME", "secure_document_db"), "USER": os.environ.get("DATABASE_USER", "postgres"), "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""), "HOST": os.environ.get("DATABASE_HOST", "localhost"), "PORT": os.environ.get("DATABASE_PORT", "5432")}}
AUTH_USER_MODEL = "authentication.User"
AUTH_PASSWORD_VALIDATORS = [{"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"}, {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"}, {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"}, {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}]
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["apps.authentication.permissions.IsActiveUser"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("JWT_ACCESS_TOKEN_MINUTES", "15"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("JWT_REFRESH_TOKEN_DAYS", "1"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = PROJECT_ROOT / "staticfiles"
MEDIA_ROOT = Path(os.environ.get("DOCUMENT_STORAGE_ROOT", str(PROJECT_ROOT / "private_media")))
MEDIA_URL = "/private-media/"
DOCUMENT_ENCRYPTION_KEY = os.environ.get("DOCUMENT_ENCRYPTION_KEY")
# Phase 6 model controls are deployment configuration, not API input.  The
# defaults make runs reproducible while allowing a security operator to tune
# the expected outlier rate without changing source code.
ANOMALY_ISOLATION_FOREST_CONTAMINATION = float(
    os.environ.get("ANOMALY_ISOLATION_FOREST_CONTAMINATION", "0.15")
)
ANOMALY_ISOLATION_FOREST_RANDOM_STATE = int(
    os.environ.get("ANOMALY_ISOLATION_FOREST_RANDOM_STATE", "42")
)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
