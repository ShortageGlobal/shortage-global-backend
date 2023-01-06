from django.contrib.auth.password_validation import validate_password, password_changed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics, permissions, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.utils import json
from rest_framework.views import APIView

from .serializers import RegistrationSerializer, ActivationSerializer, ProfileSerializer
from .models import Profile
from django.contrib.auth import get_user_model

from ..mailing.mail_service import PasswordResetEmail


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
        request_data = json.loads(request.body)
        email = request_data.get("email", None)

        if not email:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = None
        try:
            # Do not use get_object_or_404 since we don't want 404 if email doesn't exist
            user = get_user_model().objects.active().filter(email=email).get()
        except get_user_model().DoesNotExist:
            pass

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.id))

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
        request_data = json.loads(request.body)
        uid = force_str(urlsafe_base64_decode(request_data.get("uid", None)))
        token = request_data.get("token", None)

        if not uid or not token:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(get_user_model().objects.active(), pk=uid)

        if user and self.token_generator.check_token(user, token):
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


class ConfirmResetPasswordView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    def post(self, request, *args, **kwargs):
        request_data = json.loads(request.body)

        user = None
        password = request_data.get("password", None)

        if (
            request.user
            and request.user.is_authenticated
            and not request.user.is_anonymous
        ):
            user = request.user
        else:
            uid = force_str(urlsafe_base64_decode(request_data.get("uid", None)))
            token = request_data.get("token", None)

            if not uid or not token:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            user = get_object_or_404(get_user_model().objects.active(), pk=uid)

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
