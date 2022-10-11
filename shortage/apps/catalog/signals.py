from django.db.models.signals import post_save
from django.dispatch import receiver
from shortage.apps.packages.models import CartItem
from .models import Organization


@receiver(post_save, sender=Organization, dispatch_uid="remove_cart_items")
def remove_cart_items(sender, instance, **kwargs):
    """
    Remove all CartItems of the organization if it became non-public/deleted
    """
    if not instance.is_verified or instance.is_deleted:
        CartItem.objects.filter(product__organization=instance).delete()
