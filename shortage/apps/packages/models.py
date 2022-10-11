import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, URLValidator
from auditlog.registry import auditlog
from phonenumber_field.modelfields import PhoneNumberField
from thumbnails.fields import ImageField
from django_countries.fields import CountryField
from shortage.apps import storage
from shortage.apps.catalog.models import Product
from shortage.apps.file_paths import get_package_path, get_corporate_donation_path
from shortage.helpers import get_full_name


class PackageStatus(models.TextChoices):
    REGISTERED = settings.PACKAGE_STATUS["REGISTERED"], "Registered"
    PAYMENT_CANCELED = settings.PACKAGE_STATUS["PAYMENT_CANCELED"], "Payment Canceled"
    PAYMENT_FAILED = settings.PACKAGE_STATUS["PAYMENT_FAILED"], "Payment Failed"
    PAYMENT_PROCESSING = (
        settings.PACKAGE_STATUS["PAYMENT_PROCESSING"],
        "Payment Processing",
    )
    PAYMENT_SUCCEEDED = (
        settings.PACKAGE_STATUS["PAYMENT_SUCCEEDED"],
        "Payment Succeeded",
    )
    CONFIRMED = settings.PACKAGE_STATUS["CONFIRMED"], "Confirmed"
    ON_ITS_WAY = settings.PACKAGE_STATUS["ON_ITS_WAY"], "On Its Way"
    DELIVERED = settings.PACKAGE_STATUS["DELIVERED"], "Delivered"


class PackageType(models.TextChoices):
    SENT_BY_DONOR = settings.PACKAGE_TYPE["SENT_BY_DONOR"], "Sent by donor"
    FUNDED_BY_DONOR = settings.PACKAGE_TYPE["FUNDED_BY_DONOR"], "Funded by donor"


class Package(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # User can be empty because we allow anonymous donations
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="packages",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # donor details
    email = models.EmailField(max_length=100)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)

    # tax deduction
    need_tax_deduction = models.BooleanField(default=False)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state_province_region = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(default="US")

    # tracking details
    delivery_company = models.CharField(max_length=100, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)

    # payment details, only relevant for donations funded by donor
    # valid for 24 hours
    checkout_url = models.TextField(null=True, blank=True, validators=[URLValidator()])

    # package details
    note = models.TextField(null=True, blank=True)
    type = models.CharField(
        max_length=32,
        choices=PackageType.choices,
        default=PackageType.SENT_BY_DONOR,
    )
    status = models.CharField(
        max_length=32,
        choices=PackageStatus.choices,
        default=PackageStatus.REGISTERED,
    )
    photo = ImageField(
        upload_to=get_package_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
        pregenerated_sizes=["package_medium"],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid.__str__()

    @property
    def medium_photo(self):
        return self.photo.thumbnails.package_medium

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)

    def payment_canceled(self):
        self.status = PackageStatus.PAYMENT_CANCELED

    def payment_failed(self):
        self.status = PackageStatus.PAYMENT_FAILED

    def payment_processing(self):
        self.status = PackageStatus.PAYMENT_PROCESSING

    def payment_succeeded(self):
        self.status = PackageStatus.PAYMENT_SUCCEEDED

    def package_confirmed(self):
        self.status = PackageStatus.CONFIRMED

    def package_on_its_way(self):
        self.status = PackageStatus.ON_ITS_WAY

    def package_delivered(self):
        self.status = PackageStatus.DELIVERED


class PackageItem(models.Model):
    package = models.ForeignKey(Package, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        related_name="package_items",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name


class Cart(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="carts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # donor details
    email = models.EmailField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)

    # tax deduction
    need_tax_deduction = models.BooleanField(default=False)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state_province_region = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(default="US")

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid.__str__()


class CartItem(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="cart_items", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return self.product.name


class CorporateDonation(models.Model):
    company_name = models.CharField(max_length=255)
    department = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(max_length=100)
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state_province_region = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(default="US")
    description = models.CharField(max_length=255)
    quantity_description = models.CharField(max_length=255, null=True, blank=True)
    number_of_pallets = models.CharField(max_length=255, null=True, blank=True)
    estimated_value = models.CharField(max_length=100)
    url = models.URLField(max_length=255, null=True, blank=True)
    photo = ImageField(
        upload_to=get_corporate_donation_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
        pregenerated_sizes=["package_medium"],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)


auditlog.register(Package)
auditlog.register(PackageItem)
auditlog.register(Cart)
auditlog.register(CartItem)
auditlog.register(CorporateDonation)
