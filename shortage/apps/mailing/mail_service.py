import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from email.headerregistry import Address


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
        self.frontend_base_url = settings.FRONTEND_BASE_URL

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

        recipients = self._format_recipients(self.get_to())
        assert recipients, "Add at least one recipient using `add_recipient` method."

        subject = self.get_subject()
        bcc = self._format_recipients(self.get_bcc())
        message = EmailMultiAlternatives(
            subject=subject,
            body=self.get_text(),
            from_email=self._format_recipient(self.get_from()),
            to=recipients,
            bcc=bcc,
        )
        message.attach_alternative(self.get_html(), "text/html")
        result = message.send(fail_silently=True)

        if result == 0:
            logging.error(
                'Failed to send email "{0}" to {1}'.format(
                    subject, ",".join(recipients)
                )
            )
            return False

        return True

    def _format_recipients(self, recipients: list):
        if recipients == None:
            return None

        return list(map(self._format_recipient, recipients))

    def _format_recipient(self, recipient):
        name = (
            recipient["name"]
            if ("name" in recipient) and len(recipient["name"]) > 0
            else ""
        )
        username, domain = recipient["email"].split("@")
        address = Address(display_name=name, username=username, domain=domain)

        return str(address)


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
        url = "%s/organizations/%s/packages/%s" % (
            self.frontend_base_url,
            self.organization_slug,
            self.package_uuid,
        )
        return {"url": url}


class UserConfirmationEmail(MailingBackend):
    """
    Email sent on user registration to confirm their email
    """

    subject = "Confirm your registration at Shortage"
    html_template = "emails/user_confirmation.html"
    text_template = "emails/user_confirmation.txt"

    def __init__(self, first_name, last_name, uid, token):
        self.first_name = first_name
        self.last_name = last_name
        self.uid = uid
        self.token = token

        super().__init__()

    def get_context(self):
        url = "%s/users/activate?uid=%s&token=%s" % (
            self.frontend_base_url,
            self.uid,
            self.token,
        )

        return {"url": url, "full_name": self.__full_name()}

    def __full_name(self):
        if self.first_name == None and self.last_name == None:
            return None

        if self.first_name != None and self.last_name != None:
            return self.first_name + " " + self.last_name

        if self.first_name != None:
            return self.first_name

        return self.last_name
