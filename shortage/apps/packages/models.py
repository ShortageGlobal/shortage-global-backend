import uuid
from django.db import models
from django.conf import settings
from auditlog.registry import auditlog
from thumbnails.fields import ImageField
from shortage.apps import storage
from shortage.apps.file_paths import get_package_path
from shortage.apps.catalog.models import Product


class PackageStatus(models.TextChoices):
    REGISTERED = settings.PACKAGE_STATUS["REGISTERED"], "Registered"
    CONFIRMED = settings.PACKAGE_STATUS["CONFIRMED"], "Confirmed"
    DELIVERED = settings.PACKAGE_STATUS["DELIVERED"], "Delivered"


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
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=100, blank=True)
    delivery_company = models.CharField(max_length=100)
    tracking_code = models.CharField(max_length=100)
    note = models.TextField(null=True, blank=True)
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


class PackageItem(models.Model):
    package = models.ForeignKey(Package, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        related_name="package_items",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField()
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid.__str__()


class CartItem(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="cart_items", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return self.product.name


auditlog.register(Package)
auditlog.register(PackageItem)
auditlog.register(Cart)
auditlog.register(CartItem)
