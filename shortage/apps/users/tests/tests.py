from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.test import APITestCase, APIRequestFactory

from shortage.apps.users.views import (
    RequestPasswordResetView,
    CheckPasswordResetTokenView,
    ConfirmResetPasswordView,
)
from shortage.helpers.test_utilities import create_test_user


class ResetPasswordTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()

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
            "uid": self.user.id,
            "token": token,
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = CheckPasswordResetTokenView.as_view()(request)

        self.assertEqual(response.status_code, 200)

        request_data = {
            "uid": self.user.id,
            "token": token,
            "password": "testPW1@3",
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

        self.assertEqual(response.status_code, 404)

        # Test user/token mismatch
        other_user = create_test_user(email="other.user@shortage.global")
        token = PasswordResetTokenGenerator().make_token(other_user)

        request_data = {
            "uid": self.user.id,
            "token": token,
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = CheckPasswordResetTokenView.as_view()(request)

        self.assertEqual(response.status_code, 404)

        # Test user/token mismatch
        request_data = {
            "uid": self.user.id,
            "token": token,
            "password": "test2",
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = ConfirmResetPasswordView.as_view()(request)

        self.assertEqual(response.status_code, 404)

        # Test weak new password
        request_data = {
            "uid": self.user.id,
            "token": token,
            "password": "test2",
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = ConfirmResetPasswordView.as_view()(request)

        self.assertEqual(response.status_code, 404)
