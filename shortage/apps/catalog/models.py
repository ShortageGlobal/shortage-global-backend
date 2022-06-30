from statistics import mode
from django.db import models
from tinymce.models import HTMLField
from django_countries.fields import CountryField
from auditlog.registry import auditlog
from thumbnails.fields import ImageField
from shortage.apps import storage
from shortage.apps.file_paths import get_organization_path, get_product_path


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


class Instruction(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = HTMLField(null=True, blank=True)
    country = CountryField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    def __str__(self):
        return self.name
    

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


class OnlineStore(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url


auditlog.register(Organization)
auditlog.register(Instruction)
auditlog.register(Product)
auditlog.register(OnlineStore)
