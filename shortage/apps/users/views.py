from django.contrib.auth.password_validation import validate_password, password_changed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import generics, permissions, status, exceptions
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

        assert email

        user = get_object_or_404(get_user_model().objects.all(), email=email)

        if user:
            reset_email = PasswordResetEmail(
                token=self.token_generator.make_token(user), uid=user.id
            )
            reset_email.add_recipient(email)
            result = reset_email.send()

            if result:
                return Response(status=status.HTTP_200_OK)

        raise exceptions.NotFound()


class CheckPasswordResetTokenView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    def post(self, request, *args, **kwargs):
        request_data = json.loads(request.body)
        uid = request_data.get("uid", None)
        token = request_data.get("token", None)

        assert uid and token

        user = get_object_or_404(get_user_model().objects.all(), pk=uid)

        if user and self.token_generator.check_token(user, token):
            return Response(status=status.HTTP_200_OK)

        raise exceptions.NotFound()


class ConfirmResetPasswordView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    def post(self, request, *args, **kwargs):
        request_data = json.loads(request.body)
        uid = request_data.get("uid", None)
        token = request_data.get("token", None)
        password = request_data.get("password", None)

        assert uid and token and password

        user = get_object_or_404(get_user_model().objects.all(), pk=uid)

        if user and self.token_generator.check_token(user, token):
            validate_password(password=password, user=user)
            user.set_password(password)
            user.save()
            password_changed(password=password, user=user)

            return Response(status=status.HTTP_200_OK)

        raise exceptions.NotFound()
