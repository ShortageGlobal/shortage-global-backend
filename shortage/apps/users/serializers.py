from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.exceptions import APIException, NotFound
from rest_framework.validators import UniqueValidator
from shortage.apps.mailing.mail_service import UserConfirmationEmail
from phonenumber_field.serializerfields import PhoneNumberField
from shortage.helpers import get_full_name
from .models import Profile
from .tokens import user_activation_token


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True, validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    first_name = serializers.CharField(
        write_only=True, required=False, allow_blank=True, default="", min_length=1
    )
    last_name = serializers.CharField(
        write_only=True, required=False, allow_blank=True, default="", min_length=1
    )
    phone_number = PhoneNumberField(
        write_only=True, required=False, allow_blank=True, default=""
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name", "phone_number"]

    @transaction.atomic
    def create(self, validated_data):
        first_name = validated_data.get("first_name", None)
        last_name = validated_data.get("last_name", None)

        user = User.objects.create(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )
        user.set_password(validated_data["password"])
        user.save()

        profile = Profile.objects.create(
            user=user, phone_number=validated_data["phone_number"]
        )
        profile.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = user_activation_token.make_token(user)

        email = UserConfirmationEmail(
            first_name=first_name, last_name=last_name, uid=uid, token=token
        )
        email.add_recipient(
            validated_data["email"],
            name=get_full_name(first_name=first_name, last_name=last_name),
        )
        sent = email.send()

        if not sent:
            raise APIException()

        return user


class ActivationSerializer(serializers.Serializer):
    uid = serializers.RegexField(
        regex=r"^[0-9A-Za-z_\-]+$", write_only=True, required=True
    )
    token = serializers.RegexField(
        regex=r"^[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32}$", write_only=True, required=True
    )

    def create(self, validated_data):
        try:
            uid = self.__decode_uid(validated_data["uid"])
            user = User.objects.get(pk=uid)

            token = validated_data["token"]
            if not user_activation_token.check_token(user, token):
                raise serializers.ValidationError(
                    {"token": "The given token is not valid."}
                )

            user.is_active = True
            user.save()

            return user
        except (User.DoesNotExist):
            raise NotFound("User not found.")

    def __decode_uid(self, data):
        try:
            return force_str(urlsafe_base64_decode(data))
        except (TypeError, ValueError, OverflowError):
            raise serializers.ValidationError({"uid": "The given uid is not valid."})
