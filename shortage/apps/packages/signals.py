from django.db.models.signals import pre_save
from django.dispatch import receiver

from shortage.apps.mailing.mail_service import (
    PackageRegistrationEmail,
    PackageDeliveryEmail,
)
from shortage.apps.packages.models import Package, PackageStatus, PackageType


@receiver(pre_save, sender=Package, dispatch_uid="package_pre_save")
def package_pre_save(sender, **kwargs):
    new_package = kwargs["instance"]

    old_package = None
    try:
        old_package = Package.objects.get(uuid=new_package.uuid)
    except Package.DoesNotExist:
        old_package = new_package

    if old_package.status != new_package.status:
        package_status_change_handler(
            new_package, old_package.status, new_package.status
        )


def package_status_change_handler(package, old_status, new_status):
    if old_status == new_status:
        return

    first_item = package.items.all()[0]
    organization = first_item.product.organization

    status_change_email = None

    if package.status == PackageStatus.REGISTERED:
        # if package sent by donor - email him right away
        # if package funded by donor - email him on payment success
        if package.type == PackageType.SENT_BY_DONOR:
            status_change_email = PackageRegistrationEmail(
                package=package,
                organization_slug=organization.slug,
                organization_name=organization.name,
            )
    elif package.status == PackageStatus.PAYMENT_PROCESSING:
        if package.type == PackageType.FUNDED_BY_DONOR:
            # notify the donor about his payment and registered package
            status_change_email = PackageRegistrationEmail(
                package=package,
                organization_slug=organization.slug,
                organization_name=organization.name,
            )
    elif package.status == PackageStatus.DELIVERED:
        status_change_email = PackageDeliveryEmail(package=package)

    if status_change_email:
        status_change_email.add_recipient(email=package.email, name=package.full_name)
        status_change_email.send()
