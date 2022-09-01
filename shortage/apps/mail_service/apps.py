from django.apps import AppConfig


class MailServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "shortage.apps.mail_service"
    verbose_name = "Mail Service"

    # Which gateway to use when sending notifications
    # Case sensitive
    SMTP_GATEWAY = "SendPulse"
