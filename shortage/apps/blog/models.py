from django.db import models
from auditlog.registry import auditlog
from django.conf import settings
import uuid


class BlogPost(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="authors", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=1000)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.title


auditlog.register(BlogPost)
