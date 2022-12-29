from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
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

    @csrf_protect
    def post(self, request, format=None):
        user = request.user or None

        email = request.POST.get("email", "")

        user_obj = get_user_model().objects.filter(email=email)
        if email and user_obj.exists():
            user = user_obj.get()

        if user:
            email = PasswordResetEmail(
                token=self.token_generator.make_token(user), uid=user.id
            )
            result = email.send()

            if result:
                return Response(status=status.HTTP_200_OK)

        raise exceptions.NotFound()


class CheckPasswordResetTokenView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    @sensitive_post_parameters()
    @never_cache
    def post(self, request, format=None):
        uid = request.POST.get("uid", "")
        token = request.POST.get("token", "")

        assert uid and token

        user = get_user_model().objects.filter(pk=uid).get()

        if user and self.token_generator.check_token(user, token):
            return Response(status=status.HTTP_200_OK)

        raise exceptions.NotFound()


class ConfirmResetPasswordView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]
    token_generator = PasswordResetTokenGenerator()

    @sensitive_post_parameters()
    @never_cache
    def post(self, request, format=None):
        uid = request.POST.get("uid", "")
        token = request.POST.get("token", "")
        password = request.POST.get("password", "")

        assert uid and token

        user = get_user_model().objects.filter(pk=uid).get()

        if user and self.token_generator.check_token(user, token):
            user.set_password(password)
            user.save()

            return Response(status=status.HTTP_200_OK)

        raise exceptions.NotFound()
