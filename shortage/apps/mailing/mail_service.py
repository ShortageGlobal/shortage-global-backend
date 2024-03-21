import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from email.headerregistry import Address
from shortage.helpers import get_full_name


class MailingBackend:
    """
    Generic class for Mailing Backend
    """

    from_email = "support@shortage.global"
    from_name = "Shortage Team"
    subject = None
    html_template = None
    text_template = None
    to = None
    bcc = None
    attachments = None

    service_email = False
    permission_codename = None

    frontend_base_url = settings.FRONTEND_BASE_URL
    admin_base_url = settings.ADMIN_BASE_URL

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
        return self.format_email({"name": self.from_name, "email": self.from_email})

    def get_to(self):
        to = self.to if type(self.to) == list else [self.to]
        return self.format_emails(to)

    def get_bcc(self):
        return self.format_emails(self.bcc)

    def get_attachments(self):
        return self.attachments

    def add_recipient(self, email, name=""):
        assert (
            not self.service_email
        ), "Do not set recipients for service emails manually"

        self.to = self.to if self.to else []
        self.to.append({"name": name, "email": email})

    def add_bcc_recipient(self, email, name=""):
        assert (
            not self.service_email
        ), "Do not set bcc recipients for service emails manually"

        self.bcc = self.bcc if self.bcc else []
        self.bcc.append({"name": name, "email": email})

    def add_attachment(self, filename=None, content=None, mimetype=None):
        self.attachments = self.attachments if self.attachments else []
        self.attachments.append((filename, content, mimetype))

    def send(self):
        """
        Send email using SMTP
        """

        recipients = None
        if self.service_email:
            assert (
                self.permission_codename != None
            ), "Service email must have `permission_codename` property"

            users = get_user_model().objects.staff_with_permission(
                codename=self.permission_codename
            )
            recipients = [
                self.format_email({"email": user.email, "name": user.full_name})
                for user in users
            ]

            if len(recipients) == 0:
                # no users with the permission
                return False
        else:
            recipients = self.get_to()
            assert (
                recipients
            ), "Add at least one recipient using `add_recipient` method."

        message = EmailMultiAlternatives(
            subject=self.get_subject(),
            body=self.get_text(),
            from_email=self.get_from(),
            to=recipients,
            bcc=self.get_bcc(),
            attachments=self.get_attachments(),
        )

        # html version
        message.attach_alternative(self.get_html(), "text/html")

        # send email
        result = message.send(fail_silently=True)

        if result == 0:
            logging.error(
                'Failed to send email "{0}" to {1}'.format(
                    self.get_subject(), ",".join(recipients) or None
                )
            )
            return False

        return True

    def format_emails(self, recipients: list):
        if recipients == None:
            return None

        return list(map(self.format_email, recipients))

    def format_email(self, recipient):
        name = (
            recipient["name"]
            if ("name" in recipient) and len(recipient["name"]) > 0
            else ""
        )
        username, domain = recipient["email"].split("@")
        address = Address(display_name=name, username=username, domain=domain)

        return str(address)


class PackageBaseEmail(MailingBackend):
    """
    Abstract class for package-related emails
    """

    def __init__(self, package):
        self.package = package

    def get_context(self):
        package_status_url = "%s/%s/packages/%s/" % (
            self.frontend_base_url,
            self.package.organization.slug,
            self.package.uuid,
        )
        organization_url = "%s/%s/" % (
            self.frontend_base_url,
            self.package.organization.slug,
        )

        return {
            "package_status_url": package_status_url,
            "organization_url": organization_url,
            "organization": self.package.organization,
            "package": self.package,
        }


class PackageRegistrationEmail(PackageBaseEmail):
    """
    Email sent on package registration
    """

    subject = "Donation is registered - Shortage"
    html_template = "emails/package_registration/index.html"
    text_template = "emails/package_registration/index.txt"


class PackageDeliveryEmail(PackageBaseEmail):
    """
    Email sent on package delivery
    """

    subject = "Your donation was delivered - Shortage"
    html_template = "emails/package_delivered/index.html"
    text_template = "emails/package_delivered/index.txt"

    def __init__(self, package):
        super().__init__(package)

        # attach tax deduction receipt to the email if needed
        if package.need_tax_deduction and package.tax_deduction_receipt:
            # TODO: we read a file from media storage. This operation might be heavy, better to refactor some day
            self.add_attachment(
                filename="tax_deduction_receipt.pdf",
                content=package.tax_deduction_receipt.read(),
            )


class PackageRegistationServiceEmail(PackageBaseEmail):
    """
    Email sent to staff on package registration
    """

    subject = "New package is registered - Shortage"
    html_template = "emails/package_registration_staff/index.html"
    text_template = "emails/package_registration_staff/index.txt"

    service_email = True
    permission_codename = "can_receive_package_registration_emails"

    def get_context(self):
        context = super().get_context()
        context["package_admin_url"] = "%s/packages/package/%s/" % (
            self.admin_base_url,
            self.package.uuid,
        )
        context["package_items_admin_url"] = "%s/packages/packageitem/?q=%s" % (
            self.admin_base_url,
            self.package.uuid,
        )
        return context


class UserConfirmationEmail(MailingBackend):
    """
    Email sent on user registration to confirm their email
    """

    subject = "Confirm your account - Shortage"
    html_template = "emails/user_confirmation/index.html"
    text_template = "emails/user_confirmation/index.txt"

    def __init__(self, first_name, last_name, uid, token):
        self.first_name = first_name
        self.last_name = last_name
        self.uid = uid
        self.token = token

    def get_context(self):
        url = "%s/account/activate/?uid=%s&token=%s" % (
            self.frontend_base_url,
            self.uid,
            self.token,
        )

        return {
            "frontend_base_url": self.frontend_base_url,
            "url": url,
            "full_name": get_full_name(
                first_name=self.first_name,
                last_name=self.last_name,
            ),
        }


class PasswordResetEmail(MailingBackend):
    """
    Email send to the user when they request to reset password
    """

    subject = "Password Reset - Shortage"
    html_template = "emails/password_reset/index.html"
    text_template = "emails/password_reset/index.txt"

    def __init__(self, uid, token):
        self.uid = uid
        self.token = token

    def get_context(self):
        url = "%s/account/reset-password/?uid=%s&token=%s" % (
            self.frontend_base_url,
            self.uid,
            self.token,
        )

        return {
            "frontend_base_url": self.frontend_base_url,
            "url": url,
        }


class OrganizationRegistrationRequestServiceEmail(MailingBackend):
    subject = "New organization registration request - Shortage"
    html_template = "emails/organization_registration_request_staff/index.html"
    text_template = "emails/organization_registration_request_staff/index.txt"

    service_email = True
    permission_codename = "can_receive_organization_registration_request_emails"

    def __init__(self, organization_registration_request):
        self.instance = organization_registration_request

    def get_context(self):
        organization_registration_request_url = (
            "%s/catalog/organizationregistrationrequest/%s/change/"
            % (self.admin_base_url, self.instance.pk)
        )

        return {
            "organization_registration_request_url": organization_registration_request_url,
        }


class CorporateDonationRequestServiceEmail(MailingBackend):
    subject = "New corporate donation request - Shortage"
    html_template = "emails/corporate_donation_staff/index.html"
    text_template = "emails/corporate_donation_staff/index.txt"

    service_email = True
    permission_codename = "can_receive_corporate_donation_emails"

    def __init__(self, corporate_donation):
        self.instance = corporate_donation

    def get_context(self):
        corporate_donation_request_url = "%s/packages/corporatedonation/%s/change/" % (
            self.admin_base_url,
            self.instance.pk,
        )

        return {
            "corporate_donation_request_url": corporate_donation_request_url,
        }


class NonprofitRegistrationEmail(MailingBackend):
    """
    Email sent on nonprofit registration
    """

    subject = "Nonprofit is registered - Shortage"
    html_template = "emails/nonprofit_registration/index.html"
    text_template = "emails/nonprofit_registration/index.txt"

    def __init__(self, organization):
        self.organization = organization

    def get_context(self):
        organization_url = "%s/private/manage-nonprofit/%s/" % (
            self.frontend_base_url,
            self.organization.slug,
        )

        return {
            "organization_url": organization_url,
            "organization": self.organization,
        }


class OrganizationVerificationRequestServiceEmail(MailingBackend):
    """
    Email sent to staff when organization requires verification
    """

    subject = "Nonprofit needs verification - Shortage"
    html_template = "emails/organization_verification_staff/index.html"
    text_template = "emails/organization_verification_staff/index.txt"

    service_email = True
    permission_codename = "can_receive_organization_verification_request_emails"

    def __init__(self, organization):
        self.organization = organization

    def get_context(self):
        context = super().get_context()
        context["organization_admin_url"] = "%s/catalog/organization/%s/change/" % (
            self.admin_base_url,
            self.organization.pk,
        )
        context["products_admin_url"] = (
            "%s/catalog/product/?organization__id__exact=%s"
            % (
                self.admin_base_url,
                self.organization.pk,
            )
        )
        context["campaigns_admin_url"] = (
            "%s/catalog/campaign/?organization__id__exact=%s"
            % (
                self.admin_base_url,
                self.organization.pk,
            )
        )
        context["instructions_admin_url"] = (
            "%s/catalog/instruction/?organization__id__exact=%s"
            % (
                self.admin_base_url,
                self.organization.pk,
            )
        )
        context["impact_stories_admin_url"] = (
            "%s/catalog/organizationblogpost/?organization__id__exact=%s"
            % (
                self.admin_base_url,
                self.organization.pk,
            )
        )
        context["organization"] = self.organization
        return context


class OrganizationVerificationRequestEmail(MailingBackend):
    """
    Email sent when organization started verification process
    """

    subject = "Your Shortage page is on verification"
    html_template = "emails/nonprofit_verification_started/index.html"
    text_template = "emails/nonprofit_verification_started/index.txt"

    def __init__(self, organization):
        self.organization = organization

    def get_context(self):
        organization_url = "%s/private/manage-nonprofit/%s/" % (
            self.frontend_base_url,
            self.organization.slug,
        )

        return {
            "organization_url": organization_url,
            "organization": self.organization,
        }


class OrganizationIsVerifiedEmail(MailingBackend):
    """
    Email sent when organization is verified
    """

    subject = "Your Shortage page is verified and published"
    html_template = "emails/nonprofit_verified/index.html"
    text_template = "emails/nonprofit_verified/index.txt"

    def __init__(self, organization):
        self.organization = organization

    def get_context(self):
        organization_public_url = "%s/%s/" % (
            self.frontend_base_url,
            self.organization.slug,
        )

        return {
            "organization_public_url": organization_public_url,
            "organization": self.organization,
        }


class NonprofitHasNewDonationEmail(MailingBackend):
    """
    Email sent to the nonprofit about a new donation
    """

    subject = "New Donation Received via Shortage"
    html_template = "emails/nonprofit_new_donation/index.html"
    text_template = "emails/nonprofit_new_donation/index.txt"

    def __init__(self, package):
        self.package = package

    def get_context(self):
        donation_url = "%s/private/manage-nonprofit/%s/donations/%s/" % (
            self.frontend_base_url,
            self.package.organization.slug,
            self.package.uuid,
        )

        return {
            "donation_url": donation_url,
            "package": self.package,
        }
