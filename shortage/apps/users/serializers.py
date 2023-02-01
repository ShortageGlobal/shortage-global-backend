from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound
from phonenumber_field.serializerfields import PhoneNumberField
from shortage.apps.mailing.mail_service import UserConfirmationEmail
from shortage.helpers import get_full_name
from shortage.helpers.users import encode_uid, decode_uid, check_password_reset_token
from .models import Profile
from .tokens import user_activation_token


class RegistrationSerializer(serializers.ModelSerializer):
    """Register new inactive user and create a profile"""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True, required=True)
    phone_number = PhoneNumberField(
        write_only=True, required=False, allow_blank=True, default=""
    )
    agreed_to_terms_of_use = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            "email",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "phone_number",
            "agreed_to_terms_of_use",
        ]

    def validate_confirm_password(self, value):
        if value != self.initial_data["password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate_agreed_to_terms_of_use(self, value):
        if not value:
            raise serializers.ValidationError(
                "You must agree to the Terms of Use Policy."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data["email"]
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")

        User = get_user_model()
        user = User.objects.create(
            email=email,
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

        uid = encode_uid(user.pk)
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
    """Activate user account"""

    uid = serializers.RegexField(
        regex=r"^[0-9A-Za-z_\-]+$", write_only=True, required=True
    )
    token = serializers.RegexField(
        regex=r"^[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32}$", write_only=True, required=True
    )

    def create(self, validated_data):
        User = get_user_model()
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
        except User.DoesNotExist:
            raise NotFound("User not found.")

    def __decode_uid(self, data):
        try:
            return decode_uid(data)
        except (TypeError, ValueError, OverflowError):
            raise serializers.ValidationError({"uid": "The given uid is not valid."})


class UserSerializer(serializers.ModelSerializer):
    """ShortageUser serializer"""

    class Meta:
        model = get_user_model()
        fields = [
            "first_name",
            "last_name",
            "email",
        ]
        read_only_fields = ["email"]


class ProfileSerializer(serializers.ModelSerializer):
    """Get/update user profile"""

    user = UserSerializer(required=True)

    class Meta:
        model = Profile
        fields = ["user", "phone_number"]
        read_only_fields = []

    @transaction.atomic
    def update(self, instance, validated_data):
        # update user data
        user_data = validated_data.pop("user")
        user_serializer = self.fields["user"]
        user = instance.user
        user_serializer.update(user, user_data)
        # update profile data
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint of an authorized user"""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Wrong password.")
        return value

    def validate_confirm_password(self, value):
        if value != self.initial_data["new_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for confirming password reset for an unauthorized user"""

    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate_confirm_password(self, value):
        if value != self.initial_data["new_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return value

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")

        is_token_valid = check_password_reset_token(uid=uid, token=token)
        if not is_token_valid:
            raise serializers.ValidationError("Token is not valid.")

        return super().validate(attrs)
