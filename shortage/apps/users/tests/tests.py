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
            "password": "test2",
        }

        request = self.requestFactory.post("", data=request_data, format="json")
        response = ConfirmResetPasswordView.as_view()(request)

        self.assertEqual(response.status_code, 200)
