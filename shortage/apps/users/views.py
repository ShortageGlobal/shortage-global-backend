from django.contrib.auth.password_validation import validate_password, password_changed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.utils import json
from rest_framework.views import APIView
from shortage.apps.mailing.mail_service import PasswordResetEmail
from shortage.helpers.get_active_user_or_none import get_active_user_or_none
from shortage.helpers.decode_encode_uid import encode_uid, decode_uid
from .serializers import RegistrationSerializer, ActivationSerializer, ProfileSerializer
from .models import Profile


class RegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegistrationSerializer


class ActivationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ActivationSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    schema = AutoSchema(
        tags=["Profiles"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    http_method_names = ["get", "put", "head", "options"]

    def get_object(self):
        obj = generics.get_object_or_404(
            Profile.objects.prefetch_related("user"),
            user=self.request.user,
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj


class RequestPasswordResetView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    def post(self, request, *args, **kwargs):
        """Send email with the reset password link"""
        request_data = json.loads(request.body or "{}")
        email = request_data.get("email", None)

        if not email:
            raise exceptions.ParseError()

        user = get_active_user_or_none(email=email)

        if user:
            uid = encode_uid(user.id)
            reset_email = PasswordResetEmail(
                token=self.token_generator.make_token(user), uid=uid
            )
            reset_email.add_recipient(email)
            reset_email.send()

        # Always return 200 to avoid enumerating available emails via this method
        return Response(status=status.HTTP_200_OK)


class CheckPasswordResetTokenView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    def post(self, request, *args, **kwargs):
        """Check the uid/token pair is valid for resetting the password"""
        request_data = json.loads(request.body or "{}")
        uid = request_data.get("uid", None)
        token = request_data.get("token", None)

        is_token_valid = False
        try:
            pk = decode_uid(uid)
            user = get_active_user_or_none(pk=pk)
            is_token_valid = self.token_generator.check_token(user, token)
        except:
            pass

        if is_token_valid:
            return Response(status=status.HTTP_200_OK)

        raise exceptions.ParseError()


class ConfirmResetPasswordView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    def post(self, request, *args, **kwargs):
        request_data = json.loads(request.body or "{}")

        user = None
        password = request_data.get("password", None)

        if (
            request.user
            and request.user.is_authenticated
            and not request.user.is_anonymous
        ):
            user = request.user
        else:
            uid = decode_uid(request_data.get("uid", None))
            token = request_data.get("token", None)

            if not uid or not token:
                raise exceptions.ParseError()

            user = get_active_user_or_none(pk=uid)

            if not self.token_generator.check_token(user, token):
                # Reset user if the token is invalid to prevent the method from proceeding
                user = None

        if user and password:
            try:
                validate_password(password=password, user=user)
            except ValidationError as exception:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST, data=exception.messages
                )

            user.set_password(password)
            user.save()
            password_changed(password=password, user=user)

            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)
