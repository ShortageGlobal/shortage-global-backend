import socket
from shortage.settings.common import BASE_DIR
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

ALLOWED_HOSTS = [
    "localhost",
    "0.0.0.0",  # noqa: S104
    "127.0.0.1",
    "host.docker.internal",  # docker for mac access from container
    "[::1]",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "db",
        "PORT": 5432,
    }
}

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = []

# Debug tooltbar
hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

FRONTEND_BASE_URL = os.getenv("DJANGO_FRONTEND_BASE_URL", "http://localhost:8080")

EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "mailcatcher")
EMAIL_PORT = os.getenv("DJANGO_EMAIL_PORT", "1025")
