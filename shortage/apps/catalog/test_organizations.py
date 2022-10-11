from io import BytesIO

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json
from .views import PrivateOrganizationViewSet, PrivateOrganizationSlugExistsViewSet

# Todo: Move to test helpers after the merge
def create_image(
    storage, filename, size=(100, 100), image_mode="RGB", image_format="PNG"
):
    """
    Generate a test image, returning the filename that it was saved as.

    If ``storage`` is ``None``, the BytesIO containing the image data
    will be passed instead.
    """
    data = BytesIO()
    Image.new(image_mode, size).save(data, image_format)
    data.seek(0)
    if not storage:
        return data
    image_file = ContentFile(data.read())
    return storage.save(filename, image_file)


class PrivateOrganizationTestCase(APITestCase):
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

        # Verify that create response returns the same data as was sent
        self.assertEqual(self.testData["name"], json_response["name"])
        self.assertEqual(self.testData["slug"], json_response["slug"])
        self.assertEqual(self.testData["description"], json_response["description"])
        self.assertEqual(self.testData["url"], json_response["url"])
        self.assertEqual(self.testData["ein_number"], json_response["ein_number"])
        self.assertEqual(False, json_response["is_verified"])
        self.assertEqual(True, json_response["is_draft"])
        self.assertEqual(None, json_response["logo"])
        self.assertEqual(None, json_response["banner"])

        # Verify that GET returns the same data as was POSTed
        request = self.requestFactory.get("/api/private/organizations/")
        force_authenticate(request, user=self.user)
        response = PrivateOrganizationViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200, "Organization was not retrieved")

        json_response = json.loads(response.render().content)["results"][0]

        self.assertEqual(self.testData["name"], json_response["name"])
        self.assertEqual(self.testData["slug"], json_response["slug"])
        self.assertEqual(self.testData["description"], json_response["description"])
        self.assertEqual(self.testData["url"], json_response["url"])
        self.assertEqual(self.testData["ein_number"], json_response["ein_number"])
        self.assertEqual(False, json_response["is_verified"])
        self.assertEqual(True, json_response["is_draft"])
        self.assertEqual(None, json_response["logo"])
        self.assertEqual(None, json_response["banner"])

    def test_image_upload(self):
        image = create_image(None, "test_image.png")
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
