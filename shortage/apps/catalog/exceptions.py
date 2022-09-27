from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework import status


class OneOrganizationPerUser(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Only one organization per user is allowed.")
    default_code = "conflict"
