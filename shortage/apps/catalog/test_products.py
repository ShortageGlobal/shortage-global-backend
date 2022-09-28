from django.contrib.auth.models import User
from django.db.models import Count
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.catalog.models import Organization, Product
from shortage.apps.catalog.private.views import (
    PrivateProductsViewSet,
    PrivateProductsSlugExistsView,
)


def create_test_org(owner):
    testdata = {
        "name": "TestName",
        "slug": "testslug",
        "description": "Some description",
        "url": "https://www.someurl.com",
        "ein_number": "12345",
        "owner": owner,
    }

    organization = Organization(**testdata)
    organization.is_verified = True
    organization.is_draft = False

    organization.save()

    return organization


class PrivateProductsTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.requestFactory = APIRequestFactory()

        self.organization = create_test_org(self.user)

        self.assertNotEqual(self.organization.id, None, "Organization was not created")

    def get_request_route(self):
        return "/api/private/organizations/{}/products".format(self.organization.slug)

    def test_create(self):
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
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"post": "create"})(
            request, org_slug=self.organization.slug
        )

        self.assertEqual(response.status_code, 201, "Product was not created")

    def test_list(self):
        # Create test product
        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
            "organization_id": self.organization.id,
        }
        product1 = Product(**test_data)
        product1.save()

        self.assertNotEqual(product1.id, None)

        request = self.requestFactory.get(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        content = json.loads(response.render().content)

        self.assertEqual(content["count"], 1)
        self.assertEqual(content["results"][0]["slug"], product1.slug)

        # Create another product
        test_data["slug"] = "other_slug"

        product2 = Product(**test_data)
        product2.save()

        self.assertNotEqual(product2.id, None)

        request = self.requestFactory.get(
            self.get_request_route(), data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"get": "list"})(
            request, org_slug=self.organization.slug
        )

        content = json.loads(response.render().content)

        self.assertEqual(content["count"], 2)
        self.assertEqual(content["results"][0]["slug"], product1.slug)
        self.assertEqual(content["results"][1]["slug"], product2.slug)

    def test_retrieve(self):
        # Create test product
        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
            "organization_id": self.organization.id,
        }
        product = Product(**test_data)
        product.save()

        self.assertNotEqual(product.id, None)

        route = self.get_request_route() + "/" + product.slug

        request = self.requestFactory.get(route, format="json")
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"get": "retrieve"})(
            request, org_slug=self.organization.slug, slug=product.slug
        )

        content = json.loads(response.render().content)

        self.assertEqual(content["slug"], product.slug)

    def test_update(self):
        # Create test product
        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
            "organization_id": self.organization.id,
        }
        product = Product(**test_data)
        product.save()

        self.assertNotEqual(product.id, None)

        route = self.get_request_route() + "/" + product.slug

        test_data["name"] = "new_name"
        request = self.requestFactory.patch(
            route, data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"patch": "update"})(
            request, org_slug=self.organization.slug, slug=product.slug
        )

        content = json.loads(response.render().content)

        self.assertEqual(content["name"], "new_name")

    def test_delete(self):
        # Create test product
        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
            "organization_id": self.organization.id,
        }
        product = Product(**test_data)
        product.save()

        self.assertNotEqual(product.id, None)

        route = self.get_request_route() + "/" + product.slug

        test_data["name"] = "new_name"
        request = self.requestFactory.delete(
            route, data=test_data, format="json"
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsViewSet.as_view({"delete": "destroy"})(
            request, org_slug=self.organization.slug, slug=product.slug
        )

        self.assertEqual(response.status_code, 204)

        # Check that product wasn't actually deleted but soft-deleted instead
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.public().count(), 0)


class PrivateProductsSlugCheckerTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.requestFactory = APIRequestFactory()

        self.organization = create_test_org(self.user)

        self.assertNotEqual(self.organization.id, None, "Organization was not created")

        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
            "organization": self.organization,
        }
        self.product = Product(**test_data)
        self.product.save()

        self.assertNotEqual(self.product.id, None, "Product was not created")

    def get_request_route(self):
        return "/api/private/exists/organizations/{}/products/{}".format(
            self.organization.slug, self.product.slug
        )

    def test_auth(self):
        # Start slug checker tests
        request = self.requestFactory.get(self.get_request_route())
        response = PrivateProductsSlugExistsView.as_view({"get": "retrieve"})(
            request, org_slug=self.organization.slug, slug=self.product.slug
        )

        self.assertNotEqual(response.status_code, 200, "Method should require auth")

    def test_positive_case(self):
        request = self.requestFactory.get(self.get_request_route())
        force_authenticate(request, user=self.user)
        response = PrivateProductsSlugExistsView.as_view({"get": "retrieve"})(
            request, org_slug=self.organization.slug, slug=self.product.slug
        )

        self.assertEqual(response.status_code, 200, "Slug doesn't exist but should")

    def test_negative_case(self):
        request = self.requestFactory.get(
            "/api/private/exists/organizations/{}/products/{}".format(
                self.organization.slug, "wrong_slug"
            )
        )
        force_authenticate(request, user=self.user)
        response = PrivateProductsSlugExistsView.as_view({"get": "retrieve"})(
            request, org_slug=self.organization.slug, slug="wrong_slug"
        )

        self.assertEqual(response.status_code, 404, "Slug exists but shouldn't")

    def test_permissions(self):
        wrong_user = User.objects.create_user(username="wrong_user", password="12345")

        request = self.requestFactory.get(self.get_request_route())
        force_authenticate(request, user=wrong_user)
        response = PrivateProductsSlugExistsView.as_view({"get": "retrieve"})(
            request, org_slug=self.organization.slug, slug=self.product.slug
        )

        self.assertEqual(
            response.status_code,
            200,
            "Slug check takes user into account but shouldn't",
        )
