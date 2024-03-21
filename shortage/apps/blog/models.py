import uuid
from django.db import models
from django.conf import settings
from tinymce.models import HTMLField
from shortage.apps import storage
from shortage.apps.file_paths import get_blog_post_photo_path
from easy_thumbnails.fields import ThumbnailerImageField
from shortage.helpers.thumbnails import get_thumbnail_for_image


class BlogPostManager(models.Manager):
    def active(self):
        """Return blog posts which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)

    def published(self):
        """Return published blog posts"""
        return self.active().filter(is_draft=False)

    def published_or_owned(self, user=None):
        """Return either published blog posts or authored by the current user"""
        user = user if user.is_authenticated else None
        published = self.published()
        owned = self.active().filter(author=user)
        return published | owned


class BlogPost(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(class)s_authors",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=80)
    content = HTMLField()
    meta_description = models.CharField(max_length=200, null=True, blank=True)
    image = ThumbnailerImageField(
        max_length=500,
        null=True,
        blank=True,
        upload_to=get_blog_post_photo_path,
        storage=storage.MediaStorage(),
    )
    is_draft = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BlogPostManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

    @property
    def large_image(self):
        return get_thumbnail_for_image(self.image, "blog_post_large")

    @property
    def card_preview(self):
        return get_thumbnail_for_image(self.image, "card_preview")


class ShortageBlogPost(BlogPost):
    slug = models.SlugField(max_length=80, unique=True, db_index=True)

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ["-created_at"]
