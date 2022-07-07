import os
import dj_database_url

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", '').split(",")

if os.getenv("DATABASE_URL", None) is None:
    raise Exception("DATABASE_URL environment variable not defined")
DATABASES = {
    "default": dj_database_url.parse(os.environ.get("DATABASE_URL")),
}

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", '').split(",")
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
EMAIL_BACKEND = 'django_ses.SESBackend'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}
