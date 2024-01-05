from rest_framework.utils import json
from shortage.apps.catalog.models import Product
from shortage.apps.catalog.private.views import (
    PrivateProductsViewSet,
    PrivateProductsSlugExistsViewSet,
)
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_product,
    ShortageAPITestCase,
)


class PrivateProductsAPITestCase(ShortageAPITestCase):
    tested_view_class = PrivateProductsViewSet

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user()
        cls.organization = create_test_organization(
            owner=cls.user, is_draft=True, is_verified=False
        )

    def test_permissions(self):
        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "base_price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
        }
        # Can't anonymously create products
        response = self.create(request_data=test_data, org_slug=self.organization.slug)
        self.assertEqual(response.status_code, 401)

        # Can create a product after auth
        response = self.create(
            request_data=test_data, user=self.user, org_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 201)

        # Access from a different user
        other_user = create_test_user(email="other_user@shortage.global")
        response = self.create(
            request_data=test_data, user=other_user, org_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 403)

    def test_create(self):
        test_data = {
            "name": "Test Product",
            "slug": "tprod",
            "category": "VITAL_GOODS",
            "base_price": 999,
            "requested_amount": 20,
            "top_priority": False,
            "position": 1,
        }
        response = self.create(
            request_data=test_data, user=self.user, org_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 201)

        # Check that duplicates cannot be created
        response = self.create(
            request_data=test_data, user=self.user, org_slug=self.organization.slug
        )
        self.assertEqual(response.status_code, 400)

    def test_list(self):
        # Create test product
        product1 = create_test_product(organization=self.organization)

        response = self.list(user=self.user, org_slug=self.organization.slug)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        expected_response = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": product1.id,
                    "name": "Test Product",
                    "slug": "test_product",
                    "category": "VITAL_GOODS",
                    "photo": None,
                    "base_price": "999.00",
                    "requested_amount": 20,
                    "description": None,
                    "top_priority": False,
                    "is_public": True,
                    "position": 1,
                    "created_at": product1.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
            ],
        }

        self.assertEqual(content, expected_response)
        # Create another product
        product2 = create_test_product(
            organization=self.organization, slug="other_slug"
        )

        response = self.list(user=self.user, org_slug=self.organization.slug)
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        expected_response = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": product2.id,
                    "name": "Test Product",
                    "slug": "other_slug",
                    "category": "VITAL_GOODS",
                    "photo": None,
                    "base_price": "999.00",
                    "requested_amount": 20,
                    "description": None,
                    "top_priority": False,
                    "is_public": True,
                    "position": 1,
                    "created_at": product2.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
                {
                    "id": product1.id,
                    "name": "Test Product",
                    "slug": "test_product",
                    "category": "VITAL_GOODS",
                    "photo": None,
                    "base_price": "999.00",
                    "requested_amount": 20,
                    "description": None,
                    "top_priority": False,
                    "is_public": True,
                    "position": 1,
                    "created_at": product1.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
            ],
        }

        self.assertEqual(content, expected_response)

    def test_retrieve(self):
        product = create_test_product(organization=self.organization)

        response = self.retrieve(
            user=self.user, org_slug=self.organization.slug, pk=product.pk
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        expected_response = {
            "id": product.id,
            "name": "Test Product",
            "slug": "test_product",
            "category": "VITAL_GOODS",
            "photo": None,
            "base_price": "999.00",
            "requested_amount": 20,
            "description": None,
            "top_priority": False,
            "is_public": True,
            "position": 1,
            "created_at": product.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        self.assertEqual(content, expected_response)

        # Check that deleted products cannot be returned
        product.is_deleted = True
        product.save()

        response = self.retrieve(
            user=self.user, org_slug=self.organization.slug, pk=product.pk
        )
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        product = create_test_product(organization=self.organization)

        # Make sure partial update is not possible
        response = self.update(
            request_data={"name": "new_name"},
            user=self.user,
            org_slug=self.organization.slug,
            pk=product.pk,
        )

        self.assertEqual(response.status_code, 400)

        # TODO: Not sure if we should allow to actually change the product slug

        # Perform an update specifying only the required fields
        response = self.update(
            request_data={
                "name": "new_name",
                "slug": "slug2",
                "base_price": 123,
                "category": "BABY_CARE",
            },
            user=self.user,
            org_slug=self.organization.slug,
            pk=product.pk,
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        expected_response = {
            "id": product.id,
            "name": "new_name",
            "slug": "slug2",
            "category": "BABY_CARE",
            "photo": None,
            "base_price": "123.00",
            "requested_amount": product.requested_amount,
            "description": product.description,
            "top_priority": product.top_priority,
            "is_public": True,
            "position": product.position,
            "created_at": product.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        self.assertEqual(content, expected_response)

    def test_partial_update(self):
        product = create_test_product(organization=self.organization)

        response = self.partial_update(
            request_data={"name": "new_name"},
            user=self.user,
            org_slug=self.organization.slug,
            pk=product.pk,
        )
        self.assertEqual(response.status_code, 200)

        content = json.loads(response.render().content)

        expected_response = {
            "id": product.id,
            "name": "new_name",
            "slug": product.slug,
            "category": product.category,
            "photo": None,
            "base_price": "999.00",
            "requested_amount": product.requested_amount,
            "description": product.description,
            "top_priority": product.top_priority,
            "is_public": True,
            "position": product.position,
            "created_at": product.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        self.assertEqual(content, expected_response)

    def test_destroy(self):
        # Create test product
        product = create_test_product(organization=self.organization)

        # Cannot delete an object when not authenticated
        response = self.destroy(org_slug=self.organization.slug, pk=product.pk)
        self.assertEqual(response.status_code, 401)

        # Cannot delete objects which don't belong to you
        wrong_user = create_test_user(email="wrong_user@shortage.global")
        response = self.destroy(
            user=wrong_user, org_slug=self.organization.slug, pk=product.pk
        )
        self.assertEqual(response.status_code, 403)

        response = self.destroy(
            user=self.user, org_slug=self.organization.slug, pk=product.pk
        )
        self.assertEqual(response.status_code, 204)

        # Check that product wasn't actually deleted but soft-deleted instead
        self.assertEqual(Product.objects.all().count(), 1)
        self.assertEqual(Product.objects.active().count(), 0)


class PrivateProductsSlugCheckerTests(ShortageAPITestCase):
    tested_view_class = PrivateProductsSlugExistsViewSet

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user()
        cls.organization = create_test_organization(
            owner=cls.user, is_draft=True, is_verified=False
        )
        cls.product = create_test_product(organization=cls.organization)

    def test_positive_case(self):
        response = self.retrieve(
            user=self.user, org_slug=self.organization.slug, slug=self.product.slug
        )
        self.assertEqual(response.status_code, 200, "Slug doesn't exist but should")

    def test_negative_case(self):
        response = self.retrieve(
            user=self.user, org_slug=self.organization.slug, slug="wrong_slug"
        )
        self.assertEqual(response.status_code, 404, "Slug exists but shouldn't")

    def test_permissions(self):
        # Non-authorized
        response = self.retrieve(
            org_slug=self.organization.slug, slug=self.product.slug
        )
        self.assertEqual(response.status_code, 401)

        # For a slug you don't own
        wrong_user = create_test_user(email="wrong_user@shortage.global")
        response = self.retrieve(
            user=wrong_user, org_slug=self.organization.slug, slug=self.product.slug
        )
        self.assertEqual(response.status_code, 403)
