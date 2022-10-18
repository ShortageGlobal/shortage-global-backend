from django.db import models
from auditlog.registry import auditlog
from django.conf import settings
from shortage.apps.catalog.models import Organization
from shortage.apps.packages.models import Package
import uuid


class BlogPost(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    organization = models.ForeignKey(
        Organization,
        related_name="blog_posts",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="authors", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=1000)
    content = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False, db_index=True)

    packages = models.ManyToManyField(Package, related_name="blog_posts", blank=True)

    def __str__(self):
        return self.title


auditlog.register(BlogPost)
