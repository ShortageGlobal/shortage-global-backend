from rest_framework.fields import CurrentUserDefault


class AuthorizedUserOrNone(CurrentUserDefault):
    """Use current user as default or None if AnonymousUser"""

    def __call__(self, serializer_field):
        user = serializer_field.context["request"].user
        if user and user.is_authenticated:
            return user

        return None
