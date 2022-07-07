from django.conf import settings

DEBUG = True
ALLOWED_HOSTS = [
    'localhost',
    '0.0.0.0',  # noqa: S104
    '127.0.0.1',
    'host.docker.internal',  # docker for mac access from container
    '[::1]',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': settings.BASE_DIR / 'db.sqlite3',
    }
}

CSRF_TRUSTED_ORIGINS = []
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'