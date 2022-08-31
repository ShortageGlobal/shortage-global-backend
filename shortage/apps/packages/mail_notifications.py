from pysendpulse.pysendpulse import PySendPulse
import logging
from django.conf import settings


class MailNotification:

    def __init__(self, notification_type: str):
        self.notificationType = notification_type
        self.recipients = []
        self.senderName = "Notifications"
        self.senderEmail = "notifications@shortage.global"

    def add_recipient(self, recipient_name: str, recipient_address: str):
        self.recipients.append({"name": recipient_name, "email": recipient_address})

    def send(self):
        return None


class SendPulseNotification(MailNotification):

    def send(self):
        sp_api_proxy = PySendPulse(
            settings.SENDPULSE_API_ID,
            settings.SENDPULSE_API_SECRET,
            "memcached",
            memcached_host="127.0.0.1:11211"
        )

        email = self.generate_email_object()

        delivery_status = sp_api_proxy.smtp_send_mail_with_template(email)

        if not delivery_status["result"]:
            logging.error("Failed to deliver email with code: {0}".format(delivery_status))

        return delivery_status

    def get_subject_for_notification_type(self):
        subject: str = ""

        if '' == self.notificationType:
            subject = "Test email, please ignore"

        return subject

    def get_template_id_for_notification_type(self):
        template_id: str = ''

        if '' == self.notificationType:
            template_id = '93065'

        return template_id

    def generate_email_object(self):
        return {"subject": self.get_subject_for_notification_type(),
                "from": {"name": self.senderName, "email": self.senderEmail}, "to": self.recipients,
                "template": {"id": self.get_template_id_for_notification_type()}}

# {
#     "full_name": "Myself",
#     "email": "steam.trout@gmail.com",
#     "phone_number": "3",
#     "delivery_company": "4",
#     "tracking_code": "5",
#     "note": "6",
#     "photo": null,
#     "items": [ {"product": "fprod", "quantity": 1} ]
# }
