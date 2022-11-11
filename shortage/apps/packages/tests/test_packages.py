from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json
from shortage.apps.packages.models import (
    Package,
    PackageItem,
    PackageType,
    PackageStatus,
)
from shortage.apps.packages.private.views import (
    PrivateOrganizationPackagesViewSet,
    PrivateAccountPackagesViewSet,
)
from shortage.apps.packages.views import PackageCreationViewSet
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_product,
)


class PackageTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()
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
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()
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


class PrivateAccountPackages(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()
        self.organization = create_test_organization(owner=self.user)
        self.product = create_test_product(organization=self.organization)

    def create_package(self, type, owner=None):
        owner = owner or self.user
        package = Package.objects.create(owner=owner, type=type)
        PackageItem.objects.create(package=package, product=self.product, quantity=1)
        return package

    def test_retrieve_packages(self):
        # create packages
        sent_package = self.create_package(type=PackageType.SENT_BY_DONOR)
        funded_package = self.create_package(type=PackageType.FUNDED_BY_DONOR)

        # check that user can see one package in the list;
        # a funded package does not appear in the list if status is REGISTERED
        # because we create a dummy package each time users click "Order Items"
        request = self.requestFactory.get("/api/private/packages/")
        force_authenticate(request, user=self.user)
        response = PrivateAccountPackagesViewSet.as_view({"get": "list"})(
            request,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertDictContainsSubset(
            {"type": "SENT_BY_DONOR", "status": "REGISTERED"},
            response.data["results"][0],
        )

        # check that another user can't see those packages
        another_user = create_test_user(email="another@user.com")
        force_authenticate(request, user=another_user)
        response = PrivateAccountPackagesViewSet.as_view({"get": "list"})(
            request,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

        # after a funded package gets a new status it becomes visible
        funded_package.status = PackageStatus.PAYMENT_PROCESSING
        funded_package.save()
        force_authenticate(request, user=self.user)
        response = PrivateAccountPackagesViewSet.as_view({"get": "list"})(
            request,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)  # now there are two packages
        self.assertDictContainsSubset(
            {"type": "FUNDED_BY_DONOR", "status": "PAYMENT_PROCESSING"},
            response.data["results"][0],
        )
