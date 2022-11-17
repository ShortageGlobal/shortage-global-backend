from django.db.models.signals import post_save
from django.dispatch import receiver

from shortage.apps.mailing.mail_service import (
    PackageRegistrationEmail,
    PackageDeliveryEmail,
)
from shortage.apps.packages.models import Package, PackageStatus, PackageType


@receiver(post_save, sender=Package)
def package_updated(sender, **kwargs):
    package = kwargs["instance"]

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
