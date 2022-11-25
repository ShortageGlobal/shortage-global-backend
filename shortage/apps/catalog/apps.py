from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shortage.apps.catalog"
    verbose_name = "Catalog"

    def ready(self):
        # Connect signals
        from . import signals
