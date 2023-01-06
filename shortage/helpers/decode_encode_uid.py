from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


def encode_uid(data):
    return urlsafe_base64_encode(force_bytes(data))


def decode_uid(data):
    return force_str(urlsafe_base64_decode(data))
