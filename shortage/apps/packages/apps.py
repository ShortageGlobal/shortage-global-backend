from django.apps import AppConfig


class PackagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shortage.apps.packages"
    verbose_name = "Packages"

    def ready(self):
        from . import signals
