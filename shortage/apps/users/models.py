from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission
from auditlog.registry import auditlog
from phonenumber_field.modelfields import PhoneNumberField
from shortage.helpers import get_full_name


class ShortageUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

    def active(self):
        """Return all available users which have been activated"""
        return self.get_queryset().filter(is_active=True)

    def staff_with_permission(self, codename=None):
        """Return all active staff users with a permission"""
        permission = Permission.objects.get(codename=codename)
        return (
            self.get_queryset()
            .filter(is_active=True, is_staff=True)
            .filter(Q(groups__permissions=permission) | Q(user_permissions=permission))
        )


class ShortageUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True, blank=False, null=False)

    objects = ShortageUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = PhoneNumberField(null=True, blank=True)

    @property
    def nonprofit_admin(self):
        return self.user.organizations.active().exists()


auditlog.register(ShortageUser)
auditlog.register(Profile)
