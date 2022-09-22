from django.db import models
from django.contrib.auth.models import User
from auditlog.registry import auditlog
from phonenumber_field.modelfields import PhoneNumberField


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = PhoneNumberField(blank=True)


auditlog.register(Profile)
