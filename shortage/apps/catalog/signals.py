from django.db.models.signals import post_save
from django.dispatch import receiver
from shortage.apps.catalog.models import Organization
from shortage.apps.packages.models import CartItem
from shortage.apps.mailing.mail_service import (
    OrganizationRegistrationRequestServiceEmail,
    NonprofitRegistrationEmail,
)
from .models import Organization, OrganizationRegistrationRequest


@receiver(post_save, sender=Organization, dispatch_uid="remove_cart_items")
def remove_cart_items(sender, instance, **kwargs):
    """
    Remove all CartItems of the organization if it became non-public/deleted
    """
    if not instance.is_verified or instance.is_deleted:
        CartItem.objects.filter(product__organization=instance).delete()


@receiver(
    post_save,
    sender=OrganizationRegistrationRequest,
    dispatch_uid="send_email_on_org_registration_request_creation",
)
def send_email_on_org_registration_request_creation(
    sender, instance, created, **kwargs
):
    """
    Send a service email when Organization Registration Request is created
    """
    if created:
        # send service email to staff
        service_email = OrganizationRegistrationRequestServiceEmail(
            organization_registration_request=instance
        )
        service_email.send()


@receiver(
    post_save,
    sender=Organization,
    dispatch_uid="send_email_on_organization_creation",
)
def send_email_on_organization_creation(sender, instance, created, **kwargs):
    """
    Send an email when an Organization is created to the owner
    """
    if created:
        email = NonprofitRegistrationEmail(organization=instance)
        email.add_recipient(email=instance.owner.email, name=instance.owner.full_name)
        email.send()
