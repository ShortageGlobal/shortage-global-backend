from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from tinymce.models import HTMLField
from django_countries.fields import CountryField
from auditlog.registry import auditlog
from phonenumber_field.modelfields import PhoneNumberField
from thumbnails.fields import ImageField
from shortage.apps import storage
from shortage.apps.file_paths import get_organization_path, get_product_path
from shortage.helpers import get_full_name


class OrganizationManager(models.Manager):
    def promoted(self):
        """
        Return handpicked list of organizations to show on the main page
        """
        return self.public().filter(promote=True)

    def public(self):
        """Return all publicly available organizations"""
        return self.get_queryset().filter(
            is_verified=True, is_draft=False, is_deleted=False
        )

    def active(self):
        """Return all available organizations which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)


class Organization(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="organizations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = HTMLField(null=True, blank=True)
    logo = ImageField(
        upload_to=get_organization_path,
        storage=storage.MediaStorage(),
        pregenerated_sizes=["organization_logo_medium"],
    )
    banner = ImageField(
        upload_to=get_organization_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
        pregenerated_sizes=["organization_banner_medium"],
    )
    url = models.URLField(max_length=255, null=True, blank=True)
    ein_number = models.CharField(max_length=255, null=True, blank=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    is_draft = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    promote = models.BooleanField(default=False, db_index=True)
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OrganizationManager()

    def __str__(self):
        return self.name

    @property
    def medium_logo_photo(self):
        return self.logo.thumbnails.organization_logo_medium

    @property
    def medium_banner_photo(self):
        return self.banner.thumbnails.organization_banner_medium


class Instruction(models.Model):
    organization = models.ForeignKey(
        Organization, related_name="instructions", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = HTMLField(null=True, blank=True)
    country = CountryField(default="US")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductsManager(models.Manager):
    def promoted(self):
        """
        Return high demand public products for all promoted organizations.
        In the future, use a "promoted' flag or something.
        """
        return self.public().filter(
            organization_id__in=models.Subquery(
                Organization.objects.promoted().values("id")
            ),
            top_priority=True,
        )

    def public(self):
        """Return all publicly available products"""
        return self.get_queryset().filter(is_deleted=False)


class ProductCategory(models.TextChoices):
    VITAL_GOODS = settings.PRODUCT_CATEGORY["VITAL_GOODS"], "Vital Goods"
    HEALTHCARE = settings.PRODUCT_CATEGORY["HEALTHCARE"], "Healthcare"
    EDUCATION = settings.PRODUCT_CATEGORY["EDUCATION"], "Education"
    BABY_CARE = settings.PRODUCT_CATEGORY["BABY_CARE"], "Baby Care"
    SAVE_ANIMALS = settings.PRODUCT_CATEGORY["SAVE_ANIMALS"], "Save Animals"
    HOUSEHOLD_ITEMS = settings.PRODUCT_CATEGORY["HOUSEHOLD_ITEMS"], "Household Items"
    FOOD = settings.PRODUCT_CATEGORY["FOOD"], "Food"
    TOYS = settings.PRODUCT_CATEGORY["TOYS"], "Toys"


class Product(models.Model):
    organization = models.ForeignKey(
        Organization, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    category = models.CharField(
        max_length=255, choices=ProductCategory.choices, db_index=True
    )
    photo = ImageField(
        upload_to=get_product_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
        pregenerated_sizes=["product_large", "product_medium"],
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(1)]
    )
    requested_amount = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    description = HTMLField(null=True, blank=True)
    top_priority = models.BooleanField(default=False)
    position = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "organization"], name="unique_slug_organization"
            )
        ]

    def __str__(self):
        return self.name

    @property
    def large_photo(self):
        return self.photo.thumbnails.product_large

    @property
    def medium_photo(self):
        return self.photo.thumbnails.product_medium


class OrganizationRegistrationRequest(models.Model):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(max_length=100)
    organization_name = models.CharField(max_length=255, null=True, blank=True)
    ein_number = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)


auditlog.register(Organization)
auditlog.register(Instruction)
auditlog.register(Product)
auditlog.register(OrganizationRegistrationRequest)
