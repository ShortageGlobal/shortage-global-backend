import os
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import (
    MinValueValidator,
    URLValidator,
    FileExtensionValidator,
)
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from auditlog.registry import auditlog
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField
from easy_thumbnails.fields import ThumbnailerImageField
from shortage.apps import storage
from shortage.apps.catalog.models import Product, Organization, OrganizationBlogPost
from shortage.apps.file_paths import (
    get_package_path,
    get_corporate_donation_path,
    get_tax_deduction_receipt_path,
)
from shortage.helpers import get_full_name
from shortage.helpers.thumbnails import get_thumbnail_for_image
from weasyprint import HTML


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
    organization = models.ForeignKey(
        Organization, related_name="packages", on_delete=models.CASCADE
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
    tax_deduction_receipt = models.FileField(
        upload_to=get_tax_deduction_receipt_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
    )

    # tracking details
    delivery_company = models.CharField(max_length=100, null=True, blank=True)
    tracking_code = models.CharField(max_length=100, null=True, blank=True)

    # payment details, only relevant for donations funded by donor
    # valid for 24 hours
    checkout_url = models.TextField(null=True, blank=True, validators=[URLValidator()])

    # related blog posts
    blog_posts = models.ManyToManyField(
        OrganizationBlogPost,
        through="PackageBlogPost",
        through_fields=("package", "blog_post"),
    )

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
    photo = ThumbnailerImageField(
        upload_to=get_package_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            (
                "can_receive_package_registration_emails",
                "Receive emails about package registration",
            ),
        )

    def __str__(self):
        return self.uuid.__str__()

    @property
    def medium_photo(self):
        return get_thumbnail_for_image(self.photo, "package_medium")

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)

    def generate_tax_receipt(self, force=False):
        if not force and (
            not self.need_tax_deduction
            or self.status != PackageStatus.DELIVERED
            or self.tax_deduction_receipt
        ):
            return

        temp_file_path = f"{self.uuid}_tax_returns.pdf"

        # Render the template
        rendered_template = render_to_string(
            "tax_return_report.html",
            {"organization": self.organization, "package": self},
        )

        pdf_html = HTML(string=rendered_template, base_url=settings.WEASYPRINT_BASE_URI)
        pdf_html.write_pdf(temp_file_path)

        # Assign the temp file to the model field
        self.tax_deduction_receipt.save(
            "tax_return.pdf", open(temp_file_path, "rb"), save=False
        )

        # Delete the temp file
        os.remove(temp_file_path)

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


class PackageBlogPost(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    blog_post = models.ForeignKey(OrganizationBlogPost, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["package", "blog_post"]

    def clean(self):
        """Validate Package -> Blog Post relationship. Note, this method is called in django admin only"""

        # make sure package doesn't get blog posts from other organizations
        if self.package.organization != self.blog_post.organization:
            raise ValidationError(
                {"blog_post": _("This blog post belongs to another organization")}
            )


class PackageItem(models.Model):
    package = models.ForeignKey(Package, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product,
        related_name="package_items",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        if "package" in kwargs and "product" in kwargs:
            product = kwargs["product"]
            organization = kwargs["package"].organization

            if product.organization != organization:
                raise ValueError("Organization doesn't match product organization")

        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.product.name

    def total_price(self):
        return self.quantity * self.product.price


class PackageStatusLogEntry(models.Model):
    package = models.ForeignKey(
        Package, related_name="status_log", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=32,
        choices=PackageStatus.choices,
        default=PackageStatus.REGISTERED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status


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

    # terms of use
    agreed_to_terms_of_use = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.uuid.__str__()

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)


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
    photo = ThumbnailerImageField(
        upload_to=get_corporate_donation_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            (
                "can_receive_corporate_donation_emails",
                "Receive emails about corporate donations",
            ),
        )

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
