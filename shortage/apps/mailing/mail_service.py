import logging
from pysendpulse.pysendpulse import PySendPulse
from django.conf import settings
from django.template.loader import render_to_string


class MailingBackend:
    """
    Generic class for Mailing Backend using SendPulse
    See: https://login.sendpulse.com/manual/rest-api/#send-email-smtp
    """

    from_email = "notifications@shortage.global"
    from_name = "Shortage Team"
    subject = None
    html_template = None
    text_template = None
    to = None
    bcc = None

    def __init__(self):
        # instantiate SendPulse API Proxy
        self._sp_api_proxy = PySendPulse(
            settings.SENDPULSE_API_ID, settings.SENDPULSE_API_SECRET
        )

    def get_subject(self):
        assert self.subject is not None, (
            "'%s' should either include a `subject` attribute, "
            "or override the `get_subject()` method." % self.__class__.__name__
        )
        return self.subject

    def get_html_template(self):
        assert self.html_template is not None, (
            "'%s' should either include a `html_template` attribute, "
            "or override the `get_html_template()` method." % self.__class__.__name__
        )
        return self.html_template

    def get_text_template(self):
        assert self.text_template is not None, (
            "'%s' should either include a `text_template` attribute, "
            "or override the `get_text_template()` method." % self.__class__.__name__
        )
        return self.text_template

    def get_context(self):
        return {}

    def get_html(self):
        return render_to_string(self.get_html_template(), self.get_context())

    def get_text(self):
        return render_to_string(self.get_text_template(), self.get_context())

    def get_from(self):
        return {"name": self.from_name, "email": self.from_email}

    def get_to(self):
        to = self.to if type(self.to) == list else [self.to]
        return to

    def get_bcc(self):
        return self.bcc

    def add_recipient(self, email, name=""):
        self.to = self.to if self.to else []
        self.to.append({"name": name, "email": email})

    def add_bcc_recipient(self, email, name=""):
        self.bcc = self.bcc if self.bcc else []
        self.bcc.append({"name": name, "email": email})

    def send(self):
        """
        Send email using SMTP
        """

        assert self.to, "Add at least one recipient using `add_recipient` method."

        email = {
            "subject": self.get_subject(),
            "html": self.get_html(),
            "text": self.get_text(),
            "from": self.get_from(),
            "to": self.get_to(),
            "bcc": self.get_bcc(),
        }

        delivery_status = self._sp_api_proxy.smtp_send_mail(email)

        if not delivery_status.get("result"):
            logging.error(
                "Failed to deliver email with status: {0}".format(delivery_status)
            )
            return False

        return True


class PackageRegistrationEmail(MailingBackend):
    """
    Email sent on package registration
    """

    subject = "Package is registered"
    html_template = "emails/package_registration.html"
    text_template = "emails/package_registration.txt"

    def __init__(self, organization_slug, package_uuid):
        self.organization_slug = organization_slug
        self.package_uuid = package_uuid
        super().__init__()

    def get_context(self):
        url = "https://shortage.global/organizations/%s/packages/%s" % (
            self.organization_slug,
            self.package_uuid,
        )
        return {"url": url}
