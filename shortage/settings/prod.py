import sys
import os
import dj_database_url

DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

# Do not connect to database during static collection
if len(sys.argv) > 0 and sys.argv[1] != "collectstatic":
    database_url = os.getenv("DJANGO_DATABASE_URL", None)
    if database_url is None:
        raise Exception("DJANGO_DATABASE_URL environment variable not defined")
    DATABASES = {
        "default": dj_database_url.parse(database_url),
    }

CSRF_TRUSTED_ORIGINS = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
CORS_ALLOWED_ORIGINS = os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",")

# Storages
AWS_ACCESS_KEY_ID = os.getenv("DJANGO_AWS_ACCESS_KEY_ID", "")  # Space key
AWS_SECRET_ACCESS_KEY = os.getenv(
    "DJANGO_AWS_SECRET_ACCESS_KEY", ""
)  # Space secret key
AWS_STORAGE_BUCKET_NAME = os.getenv("DJANGO_AWS_STORAGE_BUCKET_NAME", "")  # Space name
AWS_DEFAULT_ACL = "public-read"
AWS_QUERYSTRING_AUTH = False
AWS_S3_ENDPOINT_URL = os.getenv("DJANGO_AWS_S3_ENDPOINT_URL", "")  # Space URL
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_STATIC_LOCATION = "static"
STATIC_URL = "%s/%s/%s/" % (
    AWS_S3_ENDPOINT_URL,
    AWS_STORAGE_BUCKET_NAME,
    AWS_STATIC_LOCATION,
)
STATICFILES_STORAGE = "shortage.apps.storage.StaticStorage"
AWS_MEDIA_LOCATION = "media"
MEDIA_URL = "%s/%s/%s/" % (
    AWS_S3_ENDPOINT_URL,
    AWS_STORAGE_BUCKET_NAME,
    AWS_MEDIA_LOCATION,
)
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
