from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from shortage.apps.mailing.mail_service import (
    PackageRegistrationEmail,
    PackageDeliveryEmail,
    PackageRegistationServiceEmail,
    CorporateDonationRequestServiceEmail,
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
        package_status_change_handler(instance)


def package_status_change_handler(package):
    # create package log entry
    PackageStatusLogEntry.objects.create(package=package, status=package.status)

    status_change_email = None
    service_status_change_email = None

    if package.status == PackageStatus.REGISTERED:
        # if package sent by donor - email him right away
        # if package funded by donor - email him on payment success
        if package.type == PackageType.SENT_BY_DONOR:
            status_change_email = PackageRegistrationEmail(package=package)
            service_status_change_email = PackageRegistationServiceEmail(
                package=package
            )
    elif package.status == PackageStatus.PAYMENT_SUCCEEDED:
        if package.type == PackageType.FUNDED_BY_DONOR:
            # notify the donor about his payment and registered package
            status_change_email = PackageRegistrationEmail(package=package)
            service_status_change_email = PackageRegistationServiceEmail(
                package=package
            )
    elif package.status == PackageStatus.DELIVERED:
        # Generate receipt before sending an email in case we want to include the link there
        package.generate_tax_receipt()

        status_change_email = PackageDeliveryEmail(package=package)

    # send email to package owner
    if status_change_email:
        status_change_email.add_recipient(email=package.email, name=package.full_name)
        status_change_email.send()

    # send service email to staff
    if service_status_change_email:
        service_status_change_email.send()


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
