import os
import dj_database_url

DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')

if os.getenv('DATABASE_URL', None) is None:
    raise Exception('DATABASE_URL environment variable not defined')
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL', '')),
}

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Storages
AWS_ACCESS_KEY_ID = os.getenv('SPACE_KEY', '')
AWS_SECRET_ACCESS_KEY = os.getenv('SPACE_SECRET_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('SPACE_NAME', '')
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_ENDPOINT_URL = os.getenv('SPACE_URL', '')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400'
}
AWS_STATIC_LOCATION = 'static'
STATIC_URL = '%s/%s' % (AWS_S3_ENDPOINT_URL, AWS_STATIC_LOCATION)
STATICFILES_STORAGE = 'shortage.apps.storage.StaticStorage'
AWS_MEDIA_LOCATION = 'media'
MEDIA_URL = '%s%s' % (AWS_S3_ENDPOINT_URL, AWS_MEDIA_LOCATION)
DEFAULT_FILE_STORAGE = 'shortage.apps.storage.MediaStorage'


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
