import uuid
from django.db import models
from auditlog.registry import auditlog
from thumbnails.fields import ImageField
from shortage.apps import storage
from shortage.apps.file_paths import get_package_path
from shortage.apps.catalog.models import Product


class DeliveryStatus(models.TextChoices):
    PENDING = '', 'Pending'
    CONFIRMED = 'Confirmed', 'Confirmed'
    DELIVERED = 'Delivered', 'Delivered'
    
    
class Package(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=100, blank=True)
    delivery_company = models.CharField(max_length=100)
    tracking_code = models.CharField(max_length=100)
    note = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        blank=True,
        null=True
    )
    photo = ImageField(upload_to=get_package_path, null=True, blank=True, storage=storage.MediaStorage())
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid.__str__()
    
    
class PackageItem(models.Model):
    package = models.ForeignKey(Package, on_delete=models.DO_NOTHING, null=True)
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=True)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.product.name


auditlog.register(Package)
auditlog.register(PackageItem)
