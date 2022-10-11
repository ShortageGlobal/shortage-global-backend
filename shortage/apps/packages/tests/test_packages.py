from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json
from shortage.apps.packages.private.views import PrivateOrganizationPackagesViewSet
from shortage.apps.packages.views import PackageCreationViewSet
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_product,
)


class PackageTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()

        self.organization = create_test_organization(owner=self.user)
        self.product = create_test_product(organization=self.organization)

    def test_create(self):
        test_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "user@email.com",
            "delivery_company": "Amazon",
            "tracking_code": "AZ12345678CD",
            "note": "",
            "items": [{"product": self.product.slug, "quantity": "1"}],
        }

        request = self.requestFactory.post(
            "api/organization/{}/packages".format(self.organization.slug),
            data=test_data,
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PackageCreationViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)

    def test_anonymous_create(self):
        test_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "user@email.com",
            "delivery_company": "Amazon",
            "tracking_code": "AZ12345678CD",
            "note": "",
            "items": [{"product": self.product.slug, "quantity": "1"}],
        }

        request = self.requestFactory.post(
            "api/organization/{}/packages".format(self.organization.slug),
            data=test_data,
            format="json",
        )
        response = PackageCreationViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)


class PrivatePackageTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()

        self.organization = create_test_organization(owner=self.user)
        self.product = create_test_product(organization=self.organization)

    def create_test_package(self):
        # Todo: Replace with database creation instead of using the request
        test_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "user@email.com",
            "delivery_company": "Amazon",
            "tracking_code": "AZ12345678CD",
            "note": "",
            "items": [{"product": self.product.slug, "quantity": "1"}],
        }

        request = self.requestFactory.post(
            "api/organization/{}/packages".format(self.organization.slug),
            data=test_data,
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PackageCreationViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)

    def test_retrieve(self):
        # Create a bunch of test packages
        for i in range(10):
            self.create_test_package()

        request = self.requestFactory.get(
            "/api/private/organization/{}/packages".format(self.organization.slug),
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationPackagesViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        content = json.loads(response.render().content)

        self.assertEqual(content["count"], 10)
