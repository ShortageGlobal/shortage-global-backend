import uuid
from django.db import models
from django.conf import settings
from tinymce.models import HTMLField
from thumbnails.fields import ImageField
from shortage.apps import storage
from shortage.apps.file_paths import get_blog_post_photo_path


class BlogPostManager(models.Manager):
    def public(self):
        """Return publicly available blog posts"""
        return self.get_queryset().filter(is_draft=False, is_deleted=False)

    def active(self):
        """Return blog posts which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)


class BlogPost(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="authors", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=80)
    content = HTMLField()
    meta_description = models.CharField(max_length=200, null=True, blank=True)
    image = ImageField(
        null=True,
        blank=True,
        upload_to=get_blog_post_photo_path,
        storage=storage.MediaStorage(),
        pregenerated_sizes=["blog_post_large", "card_preview"],
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
        return self.image.thumbnails.blog_post_large

    @property
    def card_preview(self):
        return self.image.thumbnails.card_preview
