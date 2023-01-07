from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


def encode_uid(data):
    """Encode user pk with base64"""
    return urlsafe_base64_encode(force_bytes(data))


def decode_uid(data):
    """Decode user pk with base64"""
    return force_str(urlsafe_base64_decode(data))


def get_active_user_or_none(**kwargs):
    """Return an active user of fail silently"""
    user = None
    try:
        user = get_user_model().objects.active().filter(**kwargs).get()
    except get_user_model().DoesNotExist:
        pass
    return user


def check_password_reset_token(uid=None, token=None, pk=None, user=None):
    """Check if password reset token is valid"""
    token_generator = PasswordResetTokenGenerator()
    is_token_valid = False
    try:
        pk = pk or decode_uid(uid)
        user = user or get_active_user_or_none(pk=pk)
        is_token_valid = token_generator.check_token(user, token)
    except:
        pass
    return is_token_valid
