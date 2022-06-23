import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", '').split(",")

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', "postgres"),
        'USER': os.getenv('DATABASE_USER', "postgres"),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', "postgres"),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': int(os.getenv('DATABASE_PORT', 5432)),
    }
}

CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", '').split(",")
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
