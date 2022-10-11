from django.db import models
from tinymce.models import HTMLField
from auditlog.registry import auditlog
from django.conf import settings
from shortage.apps.catalog.models import Organization


class BlogManager(models.Manager):
    def public(self):
        """Return all publicly available organizations"""
        return self.get_queryset().filter(is_published=True)


class BlogPost(models.Model):
    owner = models.ForeignKey(
        Organization,
        related_name="blog_posts",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="authors", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=1000)
    content = HTMLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False, db_index=True)

    objects = BlogManager()

    def __str__(self):
        return self.title


auditlog.register(BlogPost)
