from django.contrib.auth import get_user_model


def get_active_user_or_none(**kwargs):
    """Return an active user of fail silently"""
    user = None
    try:
        user = get_user_model().objects.active().filter(**kwargs).get()
    except get_user_model().DoesNotExist:
        pass
    return user
