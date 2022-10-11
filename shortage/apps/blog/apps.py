from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shortage.apps.blog"
    verbose_name = "Blog"
