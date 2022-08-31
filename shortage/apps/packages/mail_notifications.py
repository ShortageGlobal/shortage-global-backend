from pysendpulse.pysendpulse import PySendPulse
from django.conf import settings
import logging


class MailNotification:
    def __init__(self, notification_type: str):
        self.notificationType = notification_type.upper()
        self.recipients = []
        self.variable_substitutions = []
        self.senderName = "Notifications"
        self.senderEmail = "notifications@shortage.global"

    def add_recipient(self, recipient_name: str, recipient_address: str):
        self.recipients.append({"name": recipient_name, "email": recipient_address})

    def add_variable_substitution(self, var_name: str, var_value: str):
        self.variable_substitutions.append({"name": var_name, "value": var_value})

    def subject(self):
        subject: str = ""

        if "TEST" == self.notificationType:
            subject = "Test email, please ignore"
        else:
            raise Exception("Unknown notification type: " + self.notificationType)

        return subject

    def contents(self) -> str:
        template_path = self.__template_path_for_notification_type(
            self.notificationType
        )
        template_contents = open(template_path).read()

        # Substitute any variables
        for substitution in self.variable_substitutions:
            template_contents = template_contents.replace(
                "{{" + substitution["name"] + "}}", substitution["value"]
            )

        return template_contents

    def __template_path_for_notification_type(self, notification_type: str) -> str:
        # TODO: Not sure if this is dynamic path or not, may need to rebuild the path using variables
        return (
            "/project/shortage/apps/packages/mail_templates/"
            + notification_type.lower()
            + ".html"
        )

    def send(self):
        return None


class SendPulseNotification(MailNotification):
    def send(self):
        sp_api_proxy = PySendPulse(
            settings.DJANGO_SENDPULSE_API_ID,
            settings.DJANGO_SENDPULSE_API_SECRET,
            "memcached",
            memcached_host="127.0.0.1:11211",
        )

        # TODO: Send proper plain text contents of the template
        # Either have a separate plain text template or flatten the HTML somehow
        email = {
            "subject": self.subject(),
            "html": self.contents(),
            "text": self.contents(),
            "from": {"name": self.senderName, "email": self.senderEmail},
            "to": self.recipients,
        }

        delivery_status = sp_api_proxy.smtp_send_mail(email)

        if not delivery_status.get("result"):
            logging.error(
                "Failed to deliver email with status: {0}".format(delivery_status)
            )

        return delivery_status
