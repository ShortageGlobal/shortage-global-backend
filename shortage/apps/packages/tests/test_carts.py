from rest_framework.test import APITestCase, APIRequestFactory
from shortage.apps.packages.views import CartViewSet, CartItemViewSet
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_product,
)


class CartItemsTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()

        # create a product
        self.user1 = create_test_user()
        self.organization1 = create_test_organization(owner=self.user1)
        self.product1 = create_test_product(organization=self.organization1)

        # create a product in another organization
        self.user2 = create_test_user(username="testuser2")
        self.organization2 = create_test_organization(
            owner=self.user2, slug="test_organization2"
        )
        self.product2 = create_test_product(organization=self.organization2)

        # create cart
        request = self.requestFactory.post("api/carts", format="json")
        self.cartResponse = CartViewSet.as_view({"post": "create"})(request)
        self.cart = self.cartResponse.data

        # add 1 cart item
        request = self.requestFactory.post(
            "api/carts/{}".format(self.cart["uuid"]),
            data={
                "product_slug": self.product1.slug,
                "organization_slug": self.organization1.slug,
                "quantity": 1,
            },
            format="json",
        )
        CartItemViewSet.as_view({"post": "create"})(request, cart_pk=self.cart["uuid"])

    def test_cart_creation(self):
        self.assertEqual(self.cartResponse.status_code, 201)
        self.assertTrue(
            "uuid" in self.cart, "Cart did not return 'uuid' after creation"
        )

    def test_add_delete_update_cart_items(self):
        # add second cart item
        request = self.requestFactory.post(
            "api/carts/{}".format(self.cart["uuid"]),
            data={
                "product_slug": self.product2.slug,
                "organization_slug": self.organization2.slug,
                "quantity": 2,
            },
            format="json",
        )
        CartItemViewSet.as_view({"post": "create"})(request, cart_pk=self.cart["uuid"])

        # fetch cart
        request = self.requestFactory.get(
            "api/carts/{}".format(self.cart["uuid"]), format="json"
        )
        response = CartViewSet.as_view({"get": "retrieve"})(
            request, pk=self.cart["uuid"]
        )

        # check cart response
        self.assertEqual(response.status_code, 200)
        self.assertTrue("created_at" in response.data)
        self.assertDictContainsSubset(
            {
                "uuid": self.cart["uuid"],
                "need_tax_deduction": False,
                "first_name": None,
                "last_name": None,
                "phone_number": None,
                "email": None,
                "address_line1": None,
                "address_line2": None,
                "city": None,
                "state_province_region": None,
                "zip": None,
                "country": "US",
            },
            response.data,
        )

        # check cart items
        self.assertEqual(len(response.data["items"]), 2)
        self.assertTrue("uuid" in response.data["items"][0])
        self.assertTrue("uuid" in response.data["items"][1])
        self.assertDictContainsSubset(
            {"quantity": 1},
            response.data["items"][0],
        )
        self.assertDictContainsSubset(
            {
                "name": "Test Product",
                "slug": "test_product",
                "category": "VITAL_GOODS",
                "photo": None,
                "price": 999,
                "requested_amount": 20,
                "top_priority": False,
                "organization": {
                    "name": "TestName",
                    "slug": "test_organization",
                },
            },
            response.data["items"][0]["product"],
        )
        self.assertDictContainsSubset(
            {"quantity": 2},
            response.data["items"][1],
        )
        self.assertDictContainsSubset(
            {
                "name": "Test Product",
                "slug": "test_product",
                "category": "VITAL_GOODS",
                "photo": None,
                "price": 999,
                "requested_amount": 20,
                "top_priority": False,
                "organization": {
                    "name": "TestName",
                    "slug": "test_organization2",
                },
            },
            response.data["items"][1]["product"],
        )

        # delete cart item
        cart_item_uuid = response.data["items"][0]["uuid"]
        request = self.requestFactory.delete(
            "api/carts/{}/{}".format(self.cart["uuid"], cart_item_uuid),
            data={
                "product_slug": self.product2.slug,
                "organization_slug": self.organization2.slug,
                "quantity": 2,
            },
            format="json",
        )
        CartItemViewSet.as_view({"delete": "destroy"})(
            request, cart_pk=self.cart["uuid"], pk=cart_item_uuid
        )

        # refetch cart
        request = self.requestFactory.get(
            "api/carts/{}".format(self.cart["uuid"]), format="json"
        )
        response = CartViewSet.as_view({"get": "retrieve"})(
            request, pk=self.cart["uuid"]
        )

        # check cart items after deletion of one of them
        self.assertEqual(len(response.data["items"]), 1)
        self.assertDictContainsSubset(
            {
                "name": "Test Product",
                "slug": "test_product",
                "organization": {
                    "name": "TestName",
                    "slug": "test_organization2",  # note that the first cart item was deleted
                },
            },
            response.data["items"][0]["product"],
        )

        # update quantity of cart item
        cart_item_uuid = response.data["items"][0]["uuid"]
        request = self.requestFactory.put(
            "api/carts/{}/{}".format(self.cart["uuid"], cart_item_uuid),
            data={
                "quantity": 42,
            },
            format="json",
        )
        CartItemViewSet.as_view({"put": "update"})(
            request, cart_pk=self.cart["uuid"], pk=cart_item_uuid
        )

        # refetch cart
        request = self.requestFactory.get(
            "api/carts/{}".format(self.cart["uuid"]), format="json"
        )
        response = CartViewSet.as_view({"get": "retrieve"})(
            request, pk=self.cart["uuid"]
        )

        # check cart items after updating quantity
        self.assertDictContainsSubset(
            {"quantity": 42},
            response.data["items"][0],
        )

    def test_cart_cleanup_on_organization_unverification(self):
        # add second cart item
        request = self.requestFactory.post(
            "api/carts/{}".format(self.cart["uuid"]),
            data={
                "product_slug": self.product2.slug,
                "organization_slug": self.organization2.slug,
                "quantity": 2,
            },
            format="json",
        )
        CartItemViewSet.as_view({"post": "create"})(request, cart_pk=self.cart["uuid"])

        # fetch cart
        request = self.requestFactory.get(
            "api/carts/{}".format(self.cart["uuid"]), format="json"
        )
        response = CartViewSet.as_view({"get": "retrieve"})(
            request, pk=self.cart["uuid"]
        )

        # check cart items
        self.assertEqual(len(response.data["items"]), 2)

        # make organization need verification again
        self.organization1.is_verified = False
        self.organization1.save()

        # refetch cart
        request = self.requestFactory.get(
            "api/carts/{}".format(self.cart["uuid"]), format="json"
        )
        response = CartViewSet.as_view({"get": "retrieve"})(
            request, pk=self.cart["uuid"]
        )

        # check cart items after organization became a draft
        self.assertEqual(len(response.data["items"]), 1)
        self.assertDictContainsSubset(
            {
                "name": "Test Product",
                "slug": "test_product",
                "organization": {
                    "name": "TestName",
                    "slug": "test_organization2",  # note that the first cart item was deleted
                },
            },
            response.data["items"][0]["product"],
        )
