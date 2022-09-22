from shortage.settings.common import INSTALLED_APPS

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS.append("rest_framework.authtoken")

REST_FRAMEWORK = {"TEST_REQUEST_DEFAULT_FORMAT": "json"}
