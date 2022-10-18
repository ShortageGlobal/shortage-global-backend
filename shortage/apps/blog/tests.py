from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.blog.views import PrivateBlogPostViewSet, RelatedBlogPostsViewSet
from shortage.helpers.test_utilities import (
    create_test_organization,
    create_test_user,
    create_test_package,
)


class BlogPostTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        self.requestFactory = APIRequestFactory()
        self.organization = create_test_organization(owner=self.user)

        self.assertNotEqual(self.organization.id, None, "Organization was not created")

    def get_request_route(self):
        return "/api/private/organizations/{}/blog".format(self.organization.slug)

    def test_permissions(self):
        # Since we don't have org hierarchy set up now, author has to be the same as org owner
        author = self.user
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_published": False,
            "packages": [],
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

    def test_packages(self):
        package = create_test_package(organization=self.organization)

        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_published": False,
            "packages": [package.uuid],
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)

        response = PrivateBlogPostViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)

        request = self.requestFactory.get(
            self.get_request_route(), format="json"
        )
        force_authenticate(request, self.user)

        response = PrivateBlogPostViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.render().content)

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["packages"][0], str(package.uuid))

    def test_update(self):
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_published": False,
            "packages": [],
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)
        response = PrivateBlogPostViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.render().content)

        test_data["title"] = "New title"

        request = self.requestFactory.patch(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)
        response = PrivateBlogPostViewSet.as_view({"patch": "update"})(
            request, org_slug=self.organization.slug, pk=content["uuid"]
        )

        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        self.assertEqual(content["title"], test_data["title"])


    def test_delete(self):
        test_data = {
            "title": "Test title",
            "content": "<p>test content</p>",
            "is_published": False,
            "packages": [],
        }
        request = self.requestFactory.post(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, self.user)
        response = PrivateBlogPostViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201)

        content = json.loads(response.render().content)

        request = self.requestFactory.delete(
            self.get_request_route(), format="json"
        )
        force_authenticate(request, self.user)
        response = PrivateBlogPostViewSet.as_view({"delete": "destroy"})(
            request, org_slug=self.organization.slug, pk=content["uuid"]
        )

        self.assertEqual(response.status_code, 204)

        # Double check with get
        request = self.requestFactory.get(
            self.get_request_route(), format="json"
        )
        force_authenticate(request, self.user)
        response = PrivateBlogPostViewSet.as_view({"get": "retrieve"})(
            request, org_slug=self.organization.slug, pk=content["uuid"]
        )

        self.assertEqual(response.status_code, 404)

# class RelatedBlogPostsTestCase(APITestCase):
#     def setUp(self) -> None:
#         self.user = create_test_user()
#         self.requestFactory = APIRequestFactory()
#         self.organization = create_test_organization(owner=self.user)
#
#         self.assertNotEqual(self.organization.id, None, "Organization was not created")
#
#         self.package = create_test_package(organization=self.organization)
#
#         self.assertNotEqual(self.package.uuid, None, "Package was not created")
#
#     def get_request_route(self):
#         return "/api/private/organizations/{}/packages/{}/blog".format(self.organization.slug, self.package.uuid)
#
#     def test_related(self):
#         request = self.requestFactory.get(
#             self.get_request_route(), format="json"
#         )
#         force_authenticate(request, self.user)
#         response = RelatedBlogPostsViewSet.as_view({"get": "retrieve"})(
#             request, org_slug=self.organization.slug, uuid=str(self.package.uuid)
#         )
#
#         self.assertEqual(response.status_code, 200)


