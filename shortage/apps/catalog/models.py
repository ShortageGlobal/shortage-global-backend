import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from stdnum.us import ein
from tinymce.models import HTMLField
from django_countries.fields import CountryField
from auditlog.registry import auditlog
from phonenumber_field.modelfields import PhoneNumberField
from easy_thumbnails.fields import ThumbnailerImageField
from shortage.apps import storage
from shortage.apps.blog.models import BlogPost, BlogPostManager
from shortage.apps.file_paths import (
    get_organization_path,
    get_campaign_path,
    get_external_organization_path,
    get_product_path,
)
from shortage.helpers import get_full_name
from shortage.helpers.thumbnails import get_thumbnail_for_image


class OrganizationManager(models.Manager):
    def active(self):
        """Return all available organizations which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)

    def published(self):
        """Return all published organizations"""
        return self.active().filter(is_draft=False, is_verified=True)

    def published_or_owned(self, user=None):
        """Return either published organization or owned by the current user"""
        user = user if user.is_authenticated else None
        published = self.published()
        owned = self.active().filter(owner=user)
        return published | owned

    def editable(self):
        """Return all organizations eligible for editing"""
        return self.active().filter(is_draft=True, is_verified=False)

    def promoted(self):
        """Return handpicked list of organizations to show on the main page"""
        return self.published().filter(promote=True)


def validate_organization_slug_blacklist(value):
    if value in settings.ORGANIZATION_SLUG_BLACKLIST:
        raise ValidationError(
            "This value cannot be used.",
            params={"value": value},
        )


def validate_ein(value):
    if not ein.is_valid(value):
        raise ValidationError(
            "EIN is invalid",
            params={"value": value},
        )


class Organization(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="organizations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField(
        max_length=80,
        unique=True,
        validators=[validate_organization_slug_blacklist],
        error_messages={"unique": "This address has already been taken."},
    )
    url = models.URLField(max_length=255, null=True, blank=True)
    logo = ThumbnailerImageField(
        upload_to=get_organization_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
    )
    banner = ThumbnailerImageField(
        max_length=500,
        upload_to=get_organization_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
    )
    requested_goods = models.CharField(max_length=200, null=True, blank=True)
    mission_description = models.CharField(max_length=1000, null=True, blank=True)
    meta_description = models.CharField(max_length=200, null=True, blank=True)

    # tax information
    ein_number = models.CharField(
        max_length=255, null=True, blank=True, validators=[validate_ein]
    )
    address_line1 = models.CharField(max_length=255, null=True, blank=True)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state_province_region = models.CharField(max_length=255, null=True, blank=True)
    zip = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(default="US")
    representative_first_name = models.CharField(max_length=255, null=True, blank=True)
    representative_last_name = models.CharField(max_length=255, null=True, blank=True)
    representative_email = models.EmailField(max_length=100, null=True, blank=True)
    representative_phone_number = PhoneNumberField(null=True, blank=True)
    representative_url = models.URLField(max_length=75, null=True, blank=True)
    representative_signature = ThumbnailerImageField(
        max_length=500,
        upload_to=get_organization_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
    )
    tax_deduction_receipt_preamble = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Text added to automatically generated tax deduction receipts before the table",
    )
    tax_deduction_receipt_legal_information = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Text added to automatically generated tax deduction receipts at the end of the document",
    )

    is_verified = models.BooleanField(default=False, db_index=True)
    is_draft = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    promote = models.BooleanField(default=False, db_index=True)
    deadline = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OrganizationManager()

    class Meta:
        permissions = (
            (
                "can_receive_organization_verification_request_emails",
                "Receive organization verification request emails",
            ),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "%s/%s/" % (settings.FRONTEND_BASE_URL, self.slug)

    @property
    def medium_logo_photo(self):
        return get_thumbnail_for_image(self.logo, "organization_logo_medium")

    @property
    def medium_banner_photo(self):
        return get_thumbnail_for_image(self.banner, "organization_banner_medium")

    @property
    def representative_signature_image(self):
        return get_thumbnail_for_image(self.representative_signature, "signature")

    def can_generate_tax_receipts(self):
        """
        Check if organization is able to generate tax deduction receipts.
        Organization must have required tax information specified
        """
        return (
            bool(self.ein_number)
            and bool(self.address_line1)
            and bool(self.city)
            and bool(self.state_province_region)
            and bool(self.zip)
            and bool(self.country)
            and bool(self.representative_first_name)
            and bool(self.representative_last_name)
        )


class ExternalOrganization(models.Model):
    name = models.CharField(max_length=80)
    logo = ThumbnailerImageField(
        max_length=500,
        upload_to=get_external_organization_path,
        storage=storage.MediaStorage(),
    )
    url = models.URLField(max_length=255)
    position = models.PositiveIntegerField(
        default=0,
        blank=False,
        null=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = OrganizationManager()

    def __str__(self):
        return self.name

    @property
    def medium_logo_photo(self):
        return get_thumbnail_for_image(self.logo, "organization_logo_medium")


class Instruction(models.Model):
    organization = models.ForeignKey(
        Organization, related_name="instructions", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255)
    state_province_region = models.CharField(max_length=255)
    zip = models.CharField(max_length=100)
    country = CountryField(default="US")
    phone_number = PhoneNumberField(null=True, blank=True)
    comment = models.CharField(max_length=500, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProductsManager(models.Manager):
    def promoted(self):
        """
        Return high demand published products for all promoted organizations.
        In the future, use a "promoted' flag or something.
        """
        return self.public().filter(
            organization_id__in=models.Subquery(
                Organization.objects.promoted().values("id")
            ),
            top_priority=True,
        )

    def public(self):
        """Return all public products which have not been deleted"""
        return self.active().filter(is_public=True)

    def active(self):
        """Return all products which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)


class ProductCategory(models.TextChoices):
    VITAL_GOODS = settings.PRODUCT_CATEGORY["VITAL_GOODS"], "Vital Goods"
    HEALTHCARE = settings.PRODUCT_CATEGORY["HEALTHCARE"], "Healthcare"
    EDUCATION = settings.PRODUCT_CATEGORY["EDUCATION"], "Education"
    BABY_CARE = settings.PRODUCT_CATEGORY["BABY_CARE"], "Baby Care"
    ANIMAL_CARE = settings.PRODUCT_CATEGORY["ANIMAL_CARE"], "Animal Care"
    HOUSEHOLD_ITEMS = settings.PRODUCT_CATEGORY["HOUSEHOLD_ITEMS"], "Household Items"
    FOOD = settings.PRODUCT_CATEGORY["FOOD"], "Food"
    TOYS = settings.PRODUCT_CATEGORY["TOYS"], "Toys"
    HYGIENE = settings.PRODUCT_CATEGORY["HYGIENE"], "Hygiene"
    CLOTHES = settings.PRODUCT_CATEGORY["CLOTHES"], "Clothes"


class Product(models.Model):
    organization = models.ForeignKey(
        Organization, related_name="products", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, db_index=True)
    category = models.CharField(
        max_length=255, choices=ProductCategory.choices, db_index=True
    )
    photo = ThumbnailerImageField(
        max_length=500,
        upload_to=get_product_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
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
    is_public = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "organization"], name="unique_product_slug_organization"
            )
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "%s/%s/products/%s/" % (
            settings.FRONTEND_BASE_URL,
            self.organization.slug,
            self.slug,
        )

    @property
    def large_photo(self):
        return get_thumbnail_for_image(self.photo, "product_large")

    @property
    def medium_photo(self):
        return get_thumbnail_for_image(self.photo, "product_medium")


class CampaignsManager(models.Manager):
    def active(self):
        """Return all campaigns which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)

    def published(self):
        """Return all published campaigns"""
        return self.active().filter(is_draft=False)

    def published_or_owned(self, user=None):
        """Return either published campaigns or owned by the current user"""
        user = user if user.is_authenticated else None
        published = self.published()
        owned = self.active().filter(organization__owner=user)
        return published | owned


class Campaign(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, related_name="campaigns", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, db_index=True)
    banner = ThumbnailerImageField(
        max_length=500,
        upload_to=get_campaign_path,
        null=True,
        blank=True,
        storage=storage.MediaStorage(),
    )
    requested_goods = models.CharField(max_length=200, null=True, blank=True)
    mission_description = models.CharField(max_length=1000, null=True, blank=True)
    meta_description = models.CharField(max_length=200, null=True, blank=True)

    is_draft = models.BooleanField(default=True, db_index=True)
    is_public = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    deadline = models.DateTimeField(null=True, blank=True)

    # related products
    products = models.ManyToManyField(
        Product,
        through="CampaignProduct",
        through_fields=("campaign", "product"),
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CampaignsManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "organization"],
                name="unique_campaign_slug_organization",
            )
        ]

    def __str__(self):
        return self.name

    @property
    def banner_photo(self):
        return get_thumbnail_for_image(self.banner, "campaign_banner")

    @property
    def banner_photo_preview(self):
        return get_thumbnail_for_image(self.banner, "campaign_banner_preview")

    @property
    def products_count(self):
        return self.products.active().count()


class CampaignProduct(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "product"],
                name="unique_campaign_product",
            )
        ]

    def __str__(self):
        return f"{self.campaign.name} - {self.product.name}"

    def clean(self):
        """Validate Campaign <-> Product relationship. Note, this method is called in django admin only"""

        # make sure campaign doesn't get products from other organizations
        if self.campaign.organization != self.product.organization:
            raise ValidationError(
                {"product": _("This product belongs to another organization")}
            )


class OrganizationRegistrationRequest(models.Model):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(max_length=100)
    organization_name = models.CharField(max_length=255, null=True, blank=True)
    ein_number = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            (
                "can_receive_organization_registration_request_emails",
                "Receive emails about organization registration request",
            ),
        )

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return get_full_name(first_name=self.first_name, last_name=self.last_name)


class OrganizationBlogPostManager(BlogPostManager):
    def promoted(self):
        """
        Return handpicked list of organization blog posts to show on the main page
        """
        return self.published().filter(promote=True)


class OrganizationBlogPost(BlogPost):
    organization = models.ForeignKey(
        Organization, related_name="blog_posts", on_delete=models.CASCADE
    )
    promote = models.BooleanField(default=False, db_index=True)

    objects = OrganizationBlogPostManager()

    class Meta:
        unique_together = ["organization", "slug"]

    def __str__(self):
        return '{title} (by "{organization}")'.format(
            title=self.title, organization=self.organization
        )


auditlog.register(Organization)
auditlog.register(Campaign)
auditlog.register(Instruction)
auditlog.register(Product)
auditlog.register(OrganizationRegistrationRequest)
auditlog.register(OrganizationBlogPost)
