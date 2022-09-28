from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json
from shortage.apps.catalog.views import (
    PrivateOrganizationViewSet,
    PrivateOrganizationSlugExistsViewSet,
)
from shortage.apps.catalog.private.views import PrivateProductsViewSet


def create_test_org(owner):
    testdata = {
        "name": "TestName",
        "slug": "testslug",
        "description": "Some description",
        "url": "https://www.someurl.com",
        "ein_number": "12345",
    }

    request = APIRequestFactory().post(
        "/api/private/organizations/", data=testdata, format="json"
    )
    force_authenticate(request, user=owner)
    response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

    if 201 == response.status_code:
        return testdata["slug"]
    else:
        return None


class PrivateProductsTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.requestFactory = APIRequestFactory()

    def test_product_creation(self):
        org_slug = create_test_org(self.user)

        self.assertNotEqual(org_slug, None, "Organization was not created")

        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
        }
        request = self.requestFactory.post(
            "/api/private/organizations/{}/products".format(org_slug),
            data=test_data,
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"post": "create"})(request, org_slug=org_slug)
        print(response.render().content)

        self.assertEqual(response.status_code, 201, "Product was not created")


class PrivateProductsSlugCheckerTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.requestFactory = APIRequestFactory()

        self.testData = {
            "name": "TestName",
            "slug": "testslug",
            "description": "Some description",
            "url": "https://www.someurl.com",
            "ein_number": "12345",
        }

    def test_existence_checker(self):
        # Create test organization
        request = self.requestFactory.post(
            "/api/private/organizations/", data=self.testData, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201, "Organization was not created")

        # Start slug checker tests
        request = self.requestFactory.get("/api/private/exists/organizations/")
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug=self.testData["slug"]
        )

        self.assertNotEqual(response.status_code, 200, "Method should require auth")

        request = self.requestFactory.get("/api/private/exists/organizations/")
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug=self.testData["slug"]
        )

        self.assertEqual(response.status_code, 200, "Slug doesn't exist but should")

        request = self.requestFactory.get("/api/private/exists/organizations/")
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug="wrong_slug"
        )

        self.assertEqual(response.status_code, 404, "Slug exists but shouldn't")

        # Test for wrong user
        wrong_user = User.objects.create_user(username="wrong_user", password="12345")

        request = self.requestFactory.get("/api/private/exists/organizations/")
        force_authenticate(request, user=wrong_user)
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug=self.testData["slug"]
        )

        self.assertEqual(
            response.status_code,
            200,
            "Slug check takes user into account but shouldn't",
        )
