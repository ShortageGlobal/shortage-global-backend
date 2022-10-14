from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.blog.views import PrivateBlogPostViewSet
from shortage.helpers.test_utilities import create_test_organization, create_test_user


class BlogPostTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()
        self.organization = create_test_organization(owner=self.user)

        self.assertNotEqual(self.organization.id, None, "Organization was not created")

    def get_request_route(self):
        return "/api/private/organizations/{}/products".format(self.organization.slug)

    def test_permissions(self):
        # Since we don't have org hierarchy set up now, author has to be the same as org owner
        author = self.user
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_published": False,
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        response = PrivateBlogPostViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 401)

        force_authenticate(request, user=author)
        response = PrivateBlogPostViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)

        # Access from org owner
        request = self.requestFactory.get(self.get_request_route())
        force_authenticate(request, user=self.user)
        response = PrivateBlogPostViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 200)

        # Access from an author
        request = self.requestFactory.get(self.get_request_route())
        force_authenticate(request, user=author)

        response = PrivateBlogPostViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 200)

        # Access from a different user
        request = self.requestFactory.get(self.get_request_route())
        other_user = create_test_user(username="other_user")
        force_authenticate(request, user=other_user)

        response = PrivateBlogPostViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 403)
