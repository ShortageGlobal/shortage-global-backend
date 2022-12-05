from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.blog.views import BlogPostViewSet
from shortage.helpers.test_utilities import (
    create_test_user,
)


class BlogPostTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()

    def get_request_route(self):
        return "/api/private/blog"

    def test_permissions(self):
        # Since we don't have org hierarchy set up now, author has to be the same as org owner
        author = self.user
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_draft": True,
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        response = BlogPostViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 401)

        force_authenticate(request, user=author)
        response = BlogPostViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201)

        # Access from org owner
        request = self.requestFactory.get(self.get_request_route())
        force_authenticate(request, user=self.user)
        response = BlogPostViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)

        # Access from an author
        request = self.requestFactory.get(self.get_request_route())
        force_authenticate(request, user=author)

        response = BlogPostViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)

        # Access from a different user
        request = self.requestFactory.get(self.get_request_route())
        other_user = create_test_user(email="other_user@shortage.global")
        force_authenticate(request, user=other_user)

        response = BlogPostViewSet.as_view({"get": "list"})(request)

        self.assertEqual(response.status_code, 200)

    def test_update(self):
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_draft": True,
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)
        response = BlogPostViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.render().content)

        test_data["title"] = "New title"

        request = self.requestFactory.patch(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)
        response = BlogPostViewSet.as_view({"patch": "update"})(
            request, pk=content["uuid"]
        )

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        self.assertEqual(content["title"], test_data["title"])

    def test_delete(self):
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_draft": True,
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)
        response = BlogPostViewSet.as_view({"post": "create"})(request)

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.render().content)

        request = self.requestFactory.delete(self.get_request_route(), format="json")
        force_authenticate(request, self.user)
        response = BlogPostViewSet.as_view({"delete": "destroy"})(
            request, pk=content["uuid"]
        )

        self.assertEqual(response.status_code, 204)

        # Double check with get
        request = self.requestFactory.get(self.get_request_route(), format="json")
        force_authenticate(request, self.user)
        response = BlogPostViewSet.as_view({"get": "retrieve"})(
            request, pk=content["uuid"]
        )

        self.assertEqual(response.status_code, 404)
