from django.db.models.signals import pre_save
from django.dispatch import receiver

from shortage.apps.mailing.mail_service import (
    PackageRegistrationEmail,
    PackageDeliveryEmail,
)
from shortage.apps.packages.models import (
    Package,
    PackageStatus,
    PackageType,
    PackageStatusLogEntry,
)


@receiver(pre_save, sender=Package, dispatch_uid="package_update_handler")
def package_update_handler(sender, **kwargs):
    new_package = kwargs["instance"]
    old_package = None
    is_created = False

    try:
        old_package = sender.objects.get(uuid=new_package.uuid)
    except Package.DoesNotExist:
        is_created = True
        old_package = new_package

    if is_created or new_package.status != old_package.status:
        package_status_change_handler(
            new_package, old_package.status, new_package.status
        )


def package_status_change_handler(package, old_status, new_status):
    status_log = PackageStatusLogEntry(package=package, status=package.status)
    status_log.save()

    status_change_email = None

    if package.status == PackageStatus.REGISTERED:
        # if package sent by donor - email him right away
        # if package funded by donor - email him on payment success
        if package.type == PackageType.SENT_BY_DONOR:
            status_change_email = PackageRegistrationEmail(
                package=package,
                organization_slug=package.organization.slug,
                organization_name=package.organization.name,
            )
    elif package.status == PackageStatus.PAYMENT_SUCCEEDED:
        if package.type == PackageType.FUNDED_BY_DONOR:
            # notify the donor about his payment and registered package
            status_change_email = PackageRegistrationEmail(
                package=package,
                organization_slug=package.organization.slug,
                organization_name=package.organization.name,
            )
    elif package.status == PackageStatus.DELIVERED:
        status_change_email = PackageDeliveryEmail(package=package)

    if status_change_email:
        status_change_email.add_recipient(email=package.email, name=package.full_name)
        status_change_email.send()
