from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from shortage.apps.packages.models import Package, PackageStatusLogEntry


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

        status_log = PackageStatusLogEntry(
            package=new_package, status=new_package.status
        )
        status_log.save()
