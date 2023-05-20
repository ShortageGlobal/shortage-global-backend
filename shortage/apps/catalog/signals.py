from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from corsheaders.signals import check_request_enabled
from shortage.apps.catalog.models import Organization
from shortage.apps.packages.models import CartItem
from shortage.apps.mailing.mail_service import (
    OrganizationRegistrationRequestServiceEmail,
    NonprofitRegistrationEmail,
    OrganizationIsVerifiedEmail,
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
    Send an email to the owner when an Organization is created
    """
    if created:
        email = NonprofitRegistrationEmail(organization=instance)
        email.add_recipient(email=instance.owner.email, name=instance.owner.full_name)
        email.send()


@receiver(
    pre_save,
    sender=Organization,
    dispatch_uid="organization_is_verified",
)
def organization_is_verified(sender, instance, **kwargs):
    """
    Send an email to the owner when organization is verified
    """
    old_organization = None
    is_created = False

    try:
        old_organization = sender.objects.get(pk=instance.pk)
    except Organization.DoesNotExist:
        is_created = True
        old_organization = instance

    if instance.is_verified and (not old_organization.is_verified or is_created):
        email = OrganizationIsVerifiedEmail(instance)
        email.add_recipient(email=instance.owner.email, name=instance.owner.full_name)
        email.send()


def cors_allow_api_for_integrations(sender, request, **kwargs):
    public_org_api = request.path.startswith("/api/organizations/")
    public_available_api = request.path.startswith("/api/available/")
    return public_org_api or public_available_api


check_request_enabled.connect(
    cors_allow_api_for_integrations, dispatch_uid="cors_allow_api_for_integrations"
)
