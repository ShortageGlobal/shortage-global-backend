from pysendpulse.pysendpulse import PySendPulse
from django.conf import settings
from django.apps import apps
from django.template.loader import render_to_string
import logging
import json
import os


# To add a new notification type you need to do two things:
# 1) Add an entry in notification_types.json with the configuration for this type
# 2) Add a new template (if you need one) into /mail_templates/ folder with the same name you references in the config
#
# You can switch SMTP gateway used to send emails in app config
# Currently supported values:
# - SendPulse - will use SendPulse gateway
# - Log - will log the contents of an email to the log with DEBUG level
class MailNotification:
    def __init__(self, notification_type: str):
        self.notificationType = notification_type.lower()
        self.recipients = []
        self.variable_substitutions = {}

        # Load the configuration for the provided notification type
        config_path = (
            os.path.dirname(os.path.abspath(__file__)) + "/notification_types.json"
        )
        config = json.load(open(config_path))

        if config.get(self.notificationType):
            self.notification_config = config[self.notificationType]
        else:
            raise ValueError("Unknown notification type: " + self.notificationType)

    def add_recipient(self, recipient_name: str, recipient_address: str):
        self.recipients.append({"name": recipient_name, "email": recipient_address})

    def add_variable_substitution(self, var_name: str, var_value: str):
        self.variable_substitutions[var_name] = var_value

    def contents(self) -> str:
        template_path = (
            "/emails/" + self.notification_config["template_name"].lower() + ".html"
        )

        return render_to_string(template_path, self.variable_substitutions)

    def send(self) -> bool:
        sender_functor = self.__send_log
        smtp_gateway = apps.get_app_config("mail_service").SMTP_GATEWAY.upper()

        if "SENDPULSE" == smtp_gateway:
            sender_functor = self.__send_sendpulse
        elif "LOG" == smtp_gateway:
            sender_functor = self.__send_log
        else:
            raise ValueError("Unknown SMTP Gateway: " + smtp_gateway)

        return sender_functor()

    def __send_sendpulse(self):
        sp_api_proxy = PySendPulse(
            settings.SENDPULSE_API_ID,
            settings.SENDPULSE_API_SECRET,
            "memcached",
            memcached_host="127.0.0.1:11211",
        )

        # TODO: Send proper plain text contents of the template
        # Either have a separate plain text template or flatten the HTML somehow
        email = {
            "subject": self.notification_config["subject"],
            "html": self.contents(),
            "text": self.contents(),
            "from": {
                "name": self.notification_config["sender_name"],
                "email": self.notification_config["sender_email"],
            },
            "to": self.recipients,
        }

        delivery_status = sp_api_proxy.smtp_send_mail(email)

        if not delivery_status.get("result"):
            logging.error(
                "Failed to deliver email with status: {0}".format(delivery_status)
            )
            return False

        return True

    def __send_log(self):
        email = {
            "subject": self.notification_config["subject"],
            "html": self.contents(),
            "from": {
                "name": self.notification_config["sender_name"],
                "email": self.notification_config["sender_email"],
            },
            "to": self.recipients,
        }

        logging.debug(email)

        return True
