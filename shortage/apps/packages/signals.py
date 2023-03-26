from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from shortage.apps.mailing.mail_service import (
    PackageRegistrationEmail,
    PackageDeliveryEmail,
    PackageRegistationServiceEmail,
    CorporateDonationRequestServiceEmail,
    NonprofitHasNewDonationEmail,
)
from shortage.apps.packages.models import (
    Package,
    PackageStatus,
    PackageType,
    PackageStatusLogEntry,
    CorporateDonation,
)


@receiver(pre_save, sender=Package, dispatch_uid="package_update_handler")
def package_update_handler(sender, instance, **kwargs):
    old_package = None
    is_created = False

    try:
        old_package = sender.objects.get(uuid=instance.uuid)
    except Package.DoesNotExist:
        is_created = True
        old_package = instance

    # fire handler only if status changed
    if is_created or instance.status != old_package.status:
        package_status_change_handler(
            instance, is_created=is_created, old_package=old_package
        )


def package_status_change_handler(package, is_created=None, old_package=None):
    # create package log entry
    PackageStatusLogEntry.objects.create(package=package, status=package.status)

    donor_email = None
    nonprofit_email = None
    service_email = None

    if package.status == PackageStatus.REGISTERED:
        # if package is sent or dropped off by donor - email them right away;
        # if package is funded by donor - email them on payment success;
        # notify nonprofit right away is package was dropped of by donor;
        if package.type == PackageType.SENT_BY_DONOR:
            donor_email = PackageRegistrationEmail(package=package)
            service_email = PackageRegistationServiceEmail(package=package)
        if package.type == PackageType.DROPPED_OFF_BY_DONOR:
            donor_email = PackageRegistrationEmail(package=package)
            service_email = PackageRegistationServiceEmail(package=package)
            nonprofit_email = NonprofitHasNewDonationEmail(package)
    elif package.status == PackageStatus.PAYMENT_SUCCEEDED:
        if package.type == PackageType.FUNDED_BY_DONOR:
            # notify the donor about his payment and registered package
            donor_email = PackageRegistrationEmail(package=package)
            service_email = PackageRegistationServiceEmail(package=package)
    elif package.status in [PackageStatus.CONFIRMED, PackageStatus.ON_ITS_WAY]:
        if (
            not old_package.status
            in [
                PackageStatus.CONFIRMED,
                PackageStatus.ON_ITS_WAY,
            ]
            and not package.type == PackageType.DROPPED_OFF_BY_DONOR
        ):
            nonprofit_email = NonprofitHasNewDonationEmail(package)
    elif package.status == PackageStatus.DELIVERED:
        # Generate receipt before sending an email in case we want to include the link there
        package.generate_tax_receipt()

        donor_email = PackageDeliveryEmail(package=package)

    # send email to the package owner
    if donor_email:
        donor_email.add_recipient(email=package.email, name=package.full_name)
        donor_email.send()

    # send email to the package owner
    if nonprofit_email:
        nonprofit_owner = package.organization.owner
        nonprofit_email.add_recipient(
            email=nonprofit_owner.email, name=nonprofit_owner.full_name
        )
        nonprofit_email.send()

    # send service email to staff
    if service_email:
        service_email.send()


@receiver(
    post_save,
    sender=CorporateDonation,
    dispatch_uid="send_email_on_corporate_donation_request_creation",
)
def send_email_on_corporate_donation_request_creation(
    sender, instance, created, **kwargs
):
    """
    Send a service email when Corporate Donation is created
    """
    if created:
        # send service email to staff
        service_email = CorporateDonationRequestServiceEmail(
            corporate_donation=instance
        )
        service_email.send()
