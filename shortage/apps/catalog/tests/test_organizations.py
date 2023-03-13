from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.utils import json

from shortage.apps.catalog.models import Organization, Instruction
from shortage.apps.catalog.private.views import (
    PrivateOrganizationViewSet,
    PrivateOrganizationSlugExistsViewSet,
)
from shortage.apps.storage import MediaStorage
from shortage.helpers.test_utilities import (
    create_test_user,
    create_test_organization,
    create_test_image,
    ShortageAPITestCase,
    create_test_product,
    create_test_instruction,
)


class PrivateOrganizationTestCase(ShortageAPITestCase):
    tested_view_class = PrivateOrganizationViewSet

    @classmethod
    def setUpTestData(cls):
        cls.user = create_test_user()
        cls.test_data = {
            "name": "TestName",
            "slug": "testslug",
            "requested_goods": "a variety of goods",
            "mission_description": "We support community",
            "url": "https://www.someurl.com",
            "ein_number": "91-1144442",
        }

    def test_permissions(self):
        response = self.create(request_data=self.test_data)
        self.assertEqual(response.status_code, 401)

        organization = create_test_organization(owner=self.user)
        other_user = create_test_user(email="otheruser@shortage.global")

        response = self.retrieve(slug=organization.slug)
        self.assertEqual(response.status_code, 401)

        response = self.retrieve(slug=organization.slug, user=other_user)
        self.assertEqual(response.status_code, 404)

        response = self.list()
        self.assertEqual(response.status_code, 401)

        response = self.list(user=other_user)
        self.assertEqual(response.status_code, 200)

        response = self.destroy(slug=organization.slug)
        self.assertEqual(response.status_code, 401)

        response = self.destroy(slug=organization.slug, user=other_user)
        self.assertEqual(response.status_code, 404)

    def test_validators(self):
        test_data = self.test_data.copy()
        test_data["url"] = "incorrect_url"

        response = self.create(request_data=test_data, user=self.user)
        self.assertEqual(response.status_code, 400, "URL was not validated correctly")

        test_data = self.test_data.copy()
        test_data["logo"] = "random_logo_data"

        response = self.create(request_data=test_data, user=self.user)
        self.assertEqual(response.status_code, 400, "Logo was not validated correctly")

        ein_test_cases = [
            {"test_case": "111", "expected_result": 400},
            {"test_case": "asd91-1144442", "expected_result": 400},
            {"test_case": "91-1144442asd", "expected_result": 400},
            {"test_case": "91       1144442", "expected_result": 400},
            {"test_case": "911144442", "expected_result": 201},
        ]

        for case in ein_test_cases:
            test_data = self.test_data.copy()
            test_data["ein_number"] = case["test_case"]
            # Use a random slug each time to avoid conflicts
            test_data["slug"] = f"slug{test_data['ein_number']}"

            response = self.create(request_data=test_data, user=self.user)

            self.assertEqual(
                response.status_code,
                case["expected_result"],
                "EIN was not validated correctly",
            )

    def test_one_org_per_user(self):
        # Check that a user can only have one org
        test_data = self.test_data.copy()
        test_data["slug"] = "duplicate_slug"

        response = self.create(request_data=test_data, user=self.user)
        self.assertEqual(response.status_code, 201)

        response = self.create(request_data=test_data, user=self.user)
        self.assertEqual(response.status_code, 409)

    def test_create(self):
        response = self.create(request_data=self.test_data, user=self.user)
        self.assertEqual(response.status_code, 201)

        json_response = json.loads(response.render().content)

        expected_response = {
            "name": "TestName",
            "slug": "testslug",
            "requested_goods": "a variety of goods",
            "mission_description": "We support community",
            "meta_description": None,
            "logo": None,
            "banner": None,
            "url": "https://www.someurl.com",
            "ein_number": "91-1144442",
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
            "tax_deduction_receipt_legal_information": None,
            "tax_deduction_receipt_preamble": None,
        }

        self.assertEqual(json_response, expected_response)

        # Verify that GET returns the same data as was POSTed
        response = self.retrieve(user=self.user, slug=self.test_data["slug"])
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        organization = Organization.objects.get(slug=self.test_data["slug"])

        expected_response["created_at"] = organization.created_at.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        expected_response["updated_at"] = organization.updated_at.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )

        self.assertEqual(json_response, expected_response)

    def test_retrieve(self):
        organization = create_test_organization(owner=self.user)

        response = self.retrieve(user=self.user, slug=organization.slug)
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        expected_response = {
            "name": "TestName",
            "slug": "test_organization",
            "requested_goods": "very needed goods",
            "mission_description": "TestName helps people",
            "meta_description": None,
            "logo": None,
            "banner": None,
            "url": "https://www.579f9ed2-b0a7-11ed-afa1-0242ac120002.com",
            "ein_number": "91-1144442",
            "is_verified": True,
            "is_draft": False,
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
            "tax_deduction_receipt_preamble": None,
            "tax_deduction_receipt_legal_information": None,
            "updated_at": organization.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "created_at": organization.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        self.assertEqual(json_response, expected_response)

    def test_list(self):
        organization = create_test_organization(owner=self.user)

        # TODO: Do we really need list if a person can only have on org?
        response = self.list(user=self.user, slug=organization.slug)
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        expected_response = [
            {
                "name": "TestName",
                "slug": "test_organization",
                "requested_goods": "very needed goods",
                "mission_description": "TestName helps people",
                "meta_description": None,
                "logo": None,
                "banner": None,
                "url": "https://www.579f9ed2-b0a7-11ed-afa1-0242ac120002.com",
                "ein_number": "91-1144442",
                "is_verified": True,
                "is_draft": False,
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
                "tax_deduction_receipt_preamble": None,
                "tax_deduction_receipt_legal_information": None,
                "updated_at": organization.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "created_at": organization.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            }
        ]

        self.assertEqual(json_response, expected_response)

    def test_update(self):
        organization = create_test_organization(owner=self.user)

        # Make sure only editable orgs can be edited
        response = self.update(
            user=self.user, request_data={"description": "test"}, slug=organization.slug
        )
        self.assertEqual(response.status_code, 404)

        organization.is_draft = True
        organization.is_verified = False
        organization.save()

        response = self.update(
            user=self.user,
            request_data={
                "description": "test",
                "slug": "new_slug",
                "name": "amazing_name",
            },
            slug=organization.slug,
        )
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        expected_response = {
            "name": "amazing_name",
            "slug": "new_slug",
            "mission_description": "TestName helps people",
            "requested_goods": "very needed goods",
            "meta_description": None,
            "logo": None,
            "banner": None,
            "url": "https://www.579f9ed2-b0a7-11ed-afa1-0242ac120002.com",
            "ein_number": "91-1144442",
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
            "tax_deduction_receipt_preamble": None,
            "tax_deduction_receipt_legal_information": None,
        }

        self.assertEqual(expected_response, json_response)

    def test_partial_update(self):
        organization = create_test_organization(owner=self.user)

        # Make sure only editable orgs can be edited
        response = self.update(
            user=self.user, request_data={"description": "test"}, slug=organization.slug
        )
        self.assertEqual(response.status_code, 404)

        organization.is_draft = True
        organization.is_verified = False
        organization.save()

        # TODO: Partial updates currently do not work at all
        response = self.update(
            user=self.user,
            request_data={"description": "test"},
            slug=organization.slug,
        )
        # self.assertEqual(response.status_code, 200)
        #
        # json_response = json.loads(response.render().content)
        #
        # expected_response = {
        #     "name": organization.name,
        #     "slug": organization.slug,
        #     "description": "test",
        #     "meta_description": None,
        #     "logo": None,
        #     "banner": None,
        #     "url": organization.url,
        #     "ein_number": organization.ein_number,
        #     "is_verified": organization.is_verified,
        #     "is_draft": organization.is_draft,
        #     "promote": False,
        #     "deadline": None,
        #     "address_line1": organization.address_line1,
        #     "address_line2": organization.address_line2,
        #     "city": organization.city,
        #     "state_province_region": organization.state_province_region,
        #     "zip": organization.zip,
        #     "country": organization.country,
        #     "representative_first_name": organization.representative_first_name,
        #     "representative_last_name": organization.representative_last_name,
        #     "representative_email": organization.representative_email,
        #     "representative_phone_number": organization.representative_phone_number,
        #     "representative_signature": None,
        #     "tax_deduction_receipt_preamble": None,
        #     "tax_deduction_receipt_legal_information": None,
        # }
        #
        # self.assertEqual(expected_response, json_response)

    def test_destroy(self):
        organization = create_test_organization(owner=self.user)

        response = self.destroy(user=self.user, slug=organization.slug)
        self.assertEqual(response.status_code, 204)

        # Check that org wasn't actually deleted but soft-deleted instead
        self.assertEqual(Organization.objects.all().count(), 1)
        self.assertEqual(Organization.objects.active().count(), 0)

        # Check that we can't delete an already deleted org
        response = self.destroy(user=self.user, slug=organization.slug)
        self.assertEqual(response.status_code, 404)

        # Check that we can create a new org for the same user after old one was deleted
        response = self.create(request_data=self.test_data, user=self.user)
        self.assertEqual(response.status_code, 201)

        organization = Organization.objects.get(slug=self.test_data["slug"])

        organization.is_draft = False
        organization.is_verified = True
        organization.save()

        # Check that we can delete verified and non-draft orgs too
        response = self.destroy(user=self.user, slug=organization.slug)
        self.assertEqual(response.status_code, 204)

        self.assertEqual(Organization.objects.all().count(), 2)
        self.assertEqual(Organization.objects.active().count(), 0)

    def test_organization_slug_blacklist(self):
        test_data = self.test_data.copy()
        test_data["slug"] = "next"  # blacklisted value
        response = self.create(request_data=test_data, user=self.user)

        self.assertEqual(response.status_code, 400, "Organization was created")
        self.assertEqual(response.data["slug"][0], "This value cannot be used.")

    def test_image_upload(self):
        image = create_test_image(None, "test_image.png")
        logo_file = SimpleUploadedFile("test_image.png", image.getvalue())
        banner_file = SimpleUploadedFile("test_image.png", image.getvalue())

        test_data = self.test_data.copy()

        test_data["logo"] = logo_file
        test_data["banner"] = banner_file

        response = self.create(
            request_data=test_data,
            user=self.user,
            content_type="multipart",
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(response.status_code, 201, "Organization was not created")

    def test_organization_checklist(self):
        organization = create_test_organization(owner=self.user)

        response = self.custom_action(
            "get", "checklist", user=self.user, slug=organization.slug
        )
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        validation_errors = {
            "checklist": {
                "page": [
                    {
                        "code": "empty_logo",
                        "message": "Logo is empty.",
                        "severity": "WARNING",
                    },
                    {
                        "code": "empty_banner",
                        "message": "Banner is empty.",
                        "severity": "WARNING",
                    },
                ],
                "products": [
                    {
                        "code": "empty_products",
                        "message": "There must be at least one item requested by your organization.",
                        "severity": "ERROR",
                    }
                ],
                "instructions": [
                    {
                        "code": "no_instructions",
                        "message": "Delivery instructions are not provided. Donors must know where to send goods.",
                        "severity": "ERROR",
                    }
                ],
                "tax_information": [
                    {
                        "code": "empty_tax_information",
                        "message": "Tax information is not sufficient. Until you provide correct EIN number, address, etc. we won't be able to automatically generate tax deduction receipts for you. You are still able to upload tax receipts yourself.",
                        "severity": "WARNING",
                    }
                ],
            },
            "can_publish": False,
        }

        self.assertEqual(json_response, validation_errors)

        tmp_storage = MediaStorage()
        organization.logo = create_test_image(tmp_storage, "test_image.png")
        organization.url = "https://shortage.global"
        organization.banner = organization.logo
        organization.requested_goods = "vital goods for survival"
        organization.meta_description = "not empty"
        organization.address_line1 = "251 Little Falls Drive"
        organization.address_line2 = "Wilmington, DE, US"
        organization.city = "Wilmington"
        organization.state_province_region = "DE"
        organization.zip = "198080"
        organization.representative_first_name = "John"
        organization.representative_last_name = "Doe"
        organization.representative_email = "john.doe@gmail.com"
        organization.representative_phone_number = "+1 800 444 4444"
        organization.representative_signature = organization.logo
        organization.ein_number = "941196203"
        organization.zip = "19808"
        organization.save()

        instruction = create_test_instruction(organization=organization, city="")

        response = self.custom_action(
            "get", "checklist", user=self.user, slug=organization.slug
        )
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        validation_errors = {
            "checklist": {
                "page": [],
                "products": [
                    {
                        "code": "empty_products",
                        "message": "There must be at least one item requested by your organization.",
                        "severity": "ERROR",
                    },
                ],
                "instructions": [
                    {
                        "code": "empty_instruction_city",
                        "message": "City is empty.",
                        "severity": "ERROR",
                    }
                ],
                "tax_information": [],
            },
            "can_publish": False,
        }

        self.assertEqual(json_response, validation_errors)

        instruction.city = "New York"
        instruction.save()
        create_test_product(organization=organization)

        response = self.custom_action(
            "get", "checklist", user=self.user, slug=organization.slug
        )
        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.render().content)

        validation_errors = {
            "checklist": {
                "page": [],
                "products": [],
                "instructions": [],
                "tax_information": [],
            },
            "can_publish": True,
        }

        self.assertEqual(json_response, validation_errors)


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
