from statistics import mode
import uuid
import os
from django.db import models
from tinymce.models import HTMLField
from django_countries.fields import CountryField
from auditlog.registry import auditlog
from shortage.apps.catalog import storage
from thumbnails.fields import ImageField


def get_uuid_path(directory, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)

    return os.path.join(directory, filename)


def get_organization_path(instance, filename):
    return get_uuid_path(f'photo/organization/{str(instance.id)}/', filename)


def get_product_path(instance, filename):
    return get_uuid_path(f'photo/product/{str(instance.id)}/', filename)


def get_package_path(instance, filename):
    return get_uuid_path(f'photo/package/{str(instance.uuid)}/', filename)


class Organization(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = HTMLField(null=True, blank=True)
    photo = ImageField(upload_to=get_organization_path, null=True, blank=True, storage=storage.MediaStorage(),
                       pregenerated_sizes=["organization_medium"])
    url = models.URLField(max_length=255, null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    @property
    def thumbnails(self):
        return self.photo.thumbnails.all()


class Product(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    category= models.SmallIntegerField()
    photo = ImageField(upload_to=get_product_path, null=True, blank=True, storage=storage.MediaStorage(),
                       pregenerated_sizes=["product_large", "product_medium"])
    price = models.CharField(max_length=32, null=True, blank=True)
    requested_amount = models.PositiveIntegerField(default=0)
    description = HTMLField(null=True, blank=True)
    top_priority = models.BooleanField(default=False)
    position = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        ordering = ['position']

    def __str__(self):
        return self.name

    @property
    def thumbnails(self):
        return self.photo.thumbnails.all()


class Instruction(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = HTMLField(null=True, blank=True)
    country = CountryField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    def __str__(self):
        return self.name


class OnlineStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url


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


auditlog.register(Organization)
auditlog.register(Product)
auditlog.register(Instruction)
auditlog.register(OnlineStore)
auditlog.register(Package)
auditlog.register(PackageItem)
