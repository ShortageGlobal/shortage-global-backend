from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from shortage.apps.users.views import (
    RequestPasswordResetView,
    CheckPasswordResetTokenView,
    ConfirmResetPasswordView,
    PrivateChangePasswordView,
)
from shortage.helpers.test_utilities import create_test_user


class ResetPasswordTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()
        self.encoded_uid = urlsafe_base64_encode(force_bytes(self.user.id))

    def test_password_reset(self):
        request_data = {
            "email": self.user.email,
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = RequestPasswordResetView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        # Generate verification link since we can't get it from email
        token = PasswordResetTokenGenerator().make_token(self.user)

        request_data = {
            "uid": self.encoded_uid,
            "token": token,
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = CheckPasswordResetTokenView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        request_data = {
            "uid": self.encoded_uid,
            "token": token,
            "new_password": "testPW1@3",
            "confirm_password": "testPW1@3",
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = ConfirmResetPasswordView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_password_reset_negative(self):
        # Test user doesn't exist
        request_data = {
            "email": "random_email@gmail.com",
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = RequestPasswordResetView.as_view()(request)

        # Should also return 200
        self.assertEqual(response.status_code, 200)

        # Test user/token mismatch
        other_user = create_test_user(email="other.user@shortage.global")
        token = PasswordResetTokenGenerator().make_token(other_user)

        request_data = {
            "uid": self.encoded_uid,
            "token": token,
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = CheckPasswordResetTokenView.as_view()(request)

        self.assertEqual(response.status_code, 400)

        # Test user/token mismatch
        request_data = {
            "uid": self.encoded_uid,
            "token": token,
            "new_password": "testPW1@3",
            "confirm_password": "testPW1@3",
        }
        request = self.requestFactory.post("", data=request_data, format="json")
        response = ConfirmResetPasswordView.as_view()(request)
        self.assertEqual(response.status_code, 400)

        # Test weak new password
        token = PasswordResetTokenGenerator().make_token(self.user)
        request_data = {
            "uid": self.encoded_uid,
            "token": token,
            "new_password": "test2",
            "confirm_password": "test2",
        }
        request = self.requestFactory.post("", data=request_data, format="json")
        response = ConfirmResetPasswordView.as_view()(request)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["new_password"][0],
            "This password is too short. It must contain at least 8 characters.",
        )

    def test_password_reset_authorized_user(self):
        request_data = {
            "old_password": "Password123$",
            "new_password": "testPW1@3",
            "confirm_password": "testPW1@3",
        }

        request = self.requestFactory.put("", data=request_data, format="json")
        force_authenticate(request, user=self.user)
        response = PrivateChangePasswordView.as_view()(request)

        self.assertEqual(response.status_code, 200)
