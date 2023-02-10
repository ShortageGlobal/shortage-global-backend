from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.catalog.models import Organization
from shortage.apps.catalog.private.views import (
    PrivateOrganizationViewSet,
    PrivateOrganizationSlugExistsViewSet,
)
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_image,
)


class PrivateOrganizationTestCase(APITestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()

        self.testData = {
            "name": "TestName",
            "slug": "testslug",
            "description": "Some description",
            "url": "https://www.someurl.com",
            "ein_number": "12345",
        }

    def test_create_organization_permissions(self):
        request = self.requestFactory.post(
            "/api/private/organizations/", data=self.testData, format="json"
        )
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertNotEqual(
            response.status_code, 200, "Organization was created without auth"
        )

    def test_create_organization_validators(self):
        test_data = self.testData.copy()
        test_data["url"] = "incorrect_url"

        request = self.requestFactory.post(
            "/api/private/organizations/", data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 400, "URL was not validated correctly")

        test_data = self.testData.copy()
        test_data["logo"] = "random_logo_data"

        request = self.requestFactory.post(
            "/api/private/organizations/", data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 400, "Logo was not validated correctly")

    def test_create_organization(self):
        request = self.requestFactory.post(
            "/api/private/organizations/", data=self.testData, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201, "Organization was not created")

        json_response = json.loads(response.render().content)

        expected_response = {
            "name": "TestName",
            "slug": "testslug",
            "description": "Some description",
            "meta_description": None,
            "logo": None,
            "banner": None,
            "url": "https://www.someurl.com",
            "ein_number": "12345",
            "is_verified": False,
            "is_draft": True,
            "promote": False,
            "deadline": None,
            "address_line1": None,
            "address_line2": None,
            "city": None,
            "state_province_region": None,
            "zip": None,
            "country": "US",
            "representative_first_name": None,
            "representative_last_name": None,
            "representative_email": None,
            "representative_phone_number": None,
            "representative_signature": None,
        }

        self.assertEqual(json_response, expected_response)

        # Verify that GET returns the same data as was POSTed
        request = self.requestFactory.get("/api/private/organizations/")
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200, "Organization was not retrieved")

        json_response = json.loads(response.render().content)[0]

        organization = Organization.objects.get(slug=self.testData["slug"])

        expected_response = {
            "name": "TestName",
            "slug": "testslug",
            "description": "Some description",
            "meta_description": None,
            "logo": None,
            "banner": None,
            "url": "https://www.someurl.com",
            "ein_number": "12345",
            "is_verified": False,
            "is_draft": True,
            "promote": False,
            "deadline": None,
            "address_line1": None,
            "address_line2": None,
            "city": None,
            "state_province_region": None,
            "zip": None,
            "country": "US",
            "representative_first_name": None,
            "representative_last_name": None,
            "representative_email": None,
            "representative_phone_number": None,
            "representative_signature": None,
            "created_at": organization.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "updated_at": organization.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        self.assertEqual(json_response, expected_response)

    def test_organization_slug_blacklist(self):
        test_data = self.testData.copy()
        test_data["slug"] = "next"  # blacklisted value
        request = self.requestFactory.post(
            "/api/private/organizations/", data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 400, "Organization was created")
        self.assertEqual(response.data["slug"][0], "This value cannot be used.")

    def test_image_upload(self):
        image = create_test_image(None, "test_image.png")
        logo_file = SimpleUploadedFile("test_image.png", image.getvalue())
        banner_file = SimpleUploadedFile("test_image.png", image.getvalue())

        test_data = self.testData.copy()

        test_data["logo"] = logo_file
        test_data["banner"] = banner_file

        request = self.requestFactory.post(
            "/api/private/organizations/", data=test_data
        )
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201, "Organization was not created")


class PrivateOrganizationSlugCheckerTests(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()

        self.testData = {
            "name": "TestName",
            "slug": "testslug",
            "description": "Some description",
            "url": "https://www.someurl.com",
            "ein_number": "12345",
        }

    def test_existence_checker(self):
        organization = create_test_organization(owner=self.user)

        # Start slug checker tests
        request = self.requestFactory.get("/api/private/exists/organizations/")
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug=organization.slug
        )

        self.assertNotEqual(response.status_code, 200, "Method should require auth")

        request = self.requestFactory.get("/api/private/exists/organizations/")
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug=organization.slug
        )

        self.assertEqual(response.status_code, 200, "Slug doesn't exist but should")

        request = self.requestFactory.get("/api/private/exists/organizations/")
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug="wrong_slug"
        )

        self.assertEqual(response.status_code, 404, "Slug exists but shouldn't")

        # Test for wrong user
        wrong_user = create_test_user(email="wrong_user@shortage.global")
        request = self.requestFactory.get("/api/private/exists/organizations/")
        force_authenticate(request, user=wrong_user)
        response = PrivateOrganizationSlugExistsViewSet.as_view({"get": "retrieve"})(
            request, slug=organization.slug
        )

        self.assertEqual(response.status_code, 200)
