from django.db import models
from auditlog.registry import auditlog
from django.conf import settings
import uuid
from tinymce.models import HTMLField


class BlogPostManager(models.Manager):
    def public(self):
        """Return all publicly available blog posts"""
        return self.get_queryset().filter(is_draft=False, is_deleted=False)

    def active(self):
        """Return all blog posts which have not been deleted"""
        return self.get_queryset().filter(is_deleted=False)


class BlogPost(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="authors", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=1000)
    content = HTMLField()

    is_draft = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BlogPostManager()

    def __str__(self):
        return self.title


auditlog.register(BlogPost)
