from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import generics, permissions, status, exceptions
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.utils import json
from rest_framework.views import APIView
from shortage.apps.mailing.mail_service import PasswordResetEmail
from shortage.helpers.users import (
    encode_uid,
    decode_uid,
    get_active_user_or_none,
    check_password_reset_token,
)
from .serializers import (
    RegistrationSerializer,
    ActivationSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
)
from .models import Profile


class RegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegistrationSerializer


class ActivationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ActivationSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get user profile data"""

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
        tags=["Profiles"],
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
        tags=["Profiles"],
    )

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Check if the uid/token pair is valid for resetting the password"""
        request_data = json.loads(request.body or "{}")
        uid = request_data.get("uid", None)
        token = request_data.get("token", None)

        is_token_valid = check_password_reset_token(uid=uid, token=token)
        if is_token_valid:
            return Response(status=status.HTTP_200_OK)

        raise exceptions.ParseError()


class PrivateChangePasswordView(generics.UpdateAPIView):
    """An endpoint for changing password by an authenticated user"""

    schema = AutoSchema(
        tags=["Profiles"],
    )

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    http_method_names = ["put", "head", "options"]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # check old password
            if not user.check_password(serializer.data.get("old_password")):
                return Response(
                    {"old_password": ["Wrong password."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # set new password
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfirmResetPasswordView(APIView):
    schema = AutoSchema(
        tags=["PasswordReset"],
    )

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """Reset password if uid/token are valid"""
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            pk = decode_uid(serializer.data.get("uid"))
            user = get_active_user_or_none(pk=pk)

            # set new password
            user.set_password(serializer.data.get("new_password"))
            user.save()
            return Response(status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
