from django.conf import settings

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
