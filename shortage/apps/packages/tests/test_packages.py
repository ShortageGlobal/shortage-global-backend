from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json
from shortage.apps.packages.models import PackageType, PackageStatus, Package
from shortage.apps.packages.private.views import (
    PrivateOrganizationPackagesViewSet,
    PrivateAccountPackagesViewSet,
)
from shortage.apps.packages.views import PackageViewSet, PackageCreationViewSet
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_product,
    create_test_package,
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

    def test_tax_deduction_receipt_requirement(self):
        # check that package can be "Delivered" without tax deduction receipt
        package = create_test_package(
            self.product, need_tax_deduction=False, organization=self.organization
        )
        package.status = PackageStatus.DELIVERED
        package.clean()  # doesn't raise a validation error

        # check that package required tax deduction receipt to become "Delivered"
        package = create_test_package(
            self.product, need_tax_deduction=True, organization=self.organization
        )
        package.status = PackageStatus.DELIVERED
        self.assertRaises(ValidationError, package.clean)

        # provide receipt and error will not be raised
        package = create_test_package(
            self.product, need_tax_deduction=True, organization=self.organization
        )
        package.status = PackageStatus.DELIVERED
        package.tax_deduction_receipt = "/fake/path/to/receipt.pdf"
        package.clean()  # doesn't raise a validation error

    def test_organization_mismatch(self):
        try:
            create_test_package(
                self.product, owner=self.user, organization=self.organization
            )
        except Exception as exception:
            self.assertFalse(f"Exception when creating a valid a package: {exception}")

        other_org = create_test_organization(
            owner=self.user, name="Other org", slug="other_org"
        )
        with self.assertRaises(ValueError):
            create_test_package(self.product, owner=self.user, organization=other_org)

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

        request = self.requestFactory.post(
            "api/organization/{}/packages".format(self.organization.slug),
            data=test_data,
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = PackageCreationViewSet.as_view({"post": "create"})(
            request, org_slug=other_org.slug
        )

        self.assertEqual(response.status_code, 400)


class PrivatePackageTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()
        self.organization = create_test_organization(owner=self.user)
        self.product = create_test_product(organization=self.organization)

    def test_retrieve(self):
        # Create a bunch of test packages
        for i in range(10):
            create_test_package(
                self.product, owner=self.user, organization=self.organization
            )

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


class PrivateAccountPackagesTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()
        self.organization = create_test_organization(owner=self.user)
        self.product = create_test_product(organization=self.organization)

    def test_retrieve_packages(self):
        # create packages
        sent_package = create_test_package(
            self.product,
            type=PackageType.SENT_BY_DONOR,
            owner=self.user,
            organization=self.organization,
        )
        funded_package = create_test_package(
            self.product,
            type=PackageType.FUNDED_BY_DONOR,
            owner=self.user,
            organization=self.organization,
        )
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


class PackageStatusLogTestCase(APITestCase):
    def setUp(self) -> None:
        self.requestFactory = APIRequestFactory()
        self.user = create_test_user()
        self.organization = create_test_organization(owner=self.user)
        self.product = create_test_product(organization=self.organization)

    def test_status_log(self):
        package = create_test_package(
            self.product, owner=self.user, organization=self.organization
        )

        self.assertEqual(package.status, PackageStatus.REGISTERED)
        self.assertEqual(package.status_log.count(), 1)
        self.assertEqual(
            package.status_log.latest("created_at").status, PackageStatus.REGISTERED
        )

        package.package_confirmed()
        package.save()

        self.assertEqual(package.status, PackageStatus.CONFIRMED)
        self.assertEqual(package.status_log.count(), 2)
        self.assertEqual(
            package.status_log.latest("created_at").status, PackageStatus.CONFIRMED
        )

        package.package_delivered()
        package.save()

        self.assertEqual(package.status, PackageStatus.DELIVERED)
        self.assertEqual(package.status_log.count(), 3)
        self.assertEqual(
            package.status_log.latest("created_at").status, PackageStatus.DELIVERED
        )

    def test_multiple_packages(self):
        package_one = create_test_package(
            self.product, owner=self.user, organization=self.organization
        )
        package_two = create_test_package(
            self.product, owner=self.user, organization=self.organization
        )

        self.assertEqual(package_one.status, PackageStatus.REGISTERED)
        self.assertEqual(package_one.status_log.count(), 1)
        self.assertEqual(
            package_one.status_log.latest("created_at").status, PackageStatus.REGISTERED
        )

        self.assertEqual(package_two.status, PackageStatus.REGISTERED)
        self.assertEqual(package_two.status_log.count(), 1)
        self.assertEqual(
            package_two.status_log.latest("created_at").status, PackageStatus.REGISTERED
        )

        package_one.package_confirmed()
        package_one.save()

        package_two.package_delivered()
        package_two.save()

        self.assertEqual(package_one.status, PackageStatus.CONFIRMED)
        self.assertEqual(package_one.status_log.count(), 2)
        self.assertEqual(
            package_one.status_log.latest("created_at").status, PackageStatus.CONFIRMED
        )

        self.assertEqual(package_two.status, PackageStatus.DELIVERED)
        self.assertEqual(package_two.status_log.count(), 2)
        self.assertEqual(
            package_two.status_log.latest("created_at").status, PackageStatus.DELIVERED
        )

    def test_api_method(self):
        package = create_test_package(
            self.product, owner=self.user, organization=self.organization
        )

        request = self.requestFactory.get("/packages/status_log")
        force_authenticate(request, user=self.user)
        response = PackageViewSet.as_view({"get": "logs"})(
            request, org_slug=self.organization.slug, pk=package.uuid
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], PackageStatus.REGISTERED)

        package.package_delivered()
        package.save()

        request = self.requestFactory.get("/packages/status_log")
        force_authenticate(request, user=self.user)
        response = PackageViewSet.as_view({"get": "logs"})(
            request, org_slug=self.organization.slug, pk=package.uuid
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["status"], PackageStatus.REGISTERED)
        self.assertEqual(response.data[1]["status"], PackageStatus.DELIVERED)
