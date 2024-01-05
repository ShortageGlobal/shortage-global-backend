from django.contrib.auth import get_user_model
from rest_framework.mixins import (
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
)
from rest_framework.views import APIView

from shortage.apps.catalog.models import Organization, Product, Instruction
from shortage.apps.packages.models import Package, PackageItem, PackageType
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from rest_framework.test import APITestCase, force_authenticate, APIRequestFactory


class ShortageAPITestCase(APITestCase):
    maxDiff = None
    client_class = APIRequestFactory

    tested_view_class = None

    @classmethod
    def setUpClass(cls):
        if not cls.tested_view_class:
            raise ValueError("You must set up a tested_view_class")

        if not issubclass(cls.tested_view_class, APIView):
            raise ValueError("Your class must be a subclass of APIView")

        # Check that test case covers permissions
        if cls.tested_view_class.permission_classes and not hasattr(
            cls, "test_permissions"
        ):
            raise ValueError(
                f"Your view {cls.tested_view_class} contains custom permissions. You must define test_permissions method to test them"
            )

        # Check if CRUD tests are needed
        crud = [
            {
                "mixin": CreateModelMixin,
                "http_method": "post",
                "required_method_name": "create",
            },
            {
                "mixin": RetrieveModelMixin,
                "http_method": "get",
                "required_method_name": "retrieve",
            },
            {
                "mixin": UpdateModelMixin,
                "http_method": "put",
                "required_method_name": "update",
            },
            {
                "mixin": UpdateModelMixin,
                "http_method": "patch",
                "required_method_name": "partial_update",
            },
            {
                "mixin": DestroyModelMixin,
                "http_method": "delete",
                "required_method_name": "destroy",
            },
            {
                "mixin": ListModelMixin,
                "http_method": "get",
                "required_method_name": "list",
            },
        ]

        for item in crud:
            mixin = item["mixin"]
            http_method = item["http_method"]
            required_method = f"test_{item['required_method_name']}"

            if (
                issubclass(cls.tested_view_class, mixin)
                and http_method in cls.tested_view_class.http_method_names
                and not hasattr(cls, required_method)
            ):
                raise ValueError(
                    f"Your view {cls.tested_view_class} contains has {mixin} and must define {required_method} to test it"
                )

        super().setUpClass()

    def create(self, request_data=None, user=None, content_type="json", **kwargs):
        return self.custom_action(
            "post", "create", request_data, user, content_type, **kwargs
        )

    def retrieve(self, request_data=None, user=None, content_type="json", **kwargs):
        return self.custom_action(
            "get", "retrieve", request_data, user, content_type, **kwargs
        )

    def list(self, request_data=None, user=None, content_type="json", **kwargs):
        return self.custom_action(
            "get", "list", request_data, user, content_type, **kwargs
        )

    def update(self, request_data=None, user=None, content_type="json", **kwargs):
        return self.custom_action(
            "put", "update", request_data, user, content_type, **kwargs
        )

    def partial_update(
        self, request_data=None, user=None, content_type="json", **kwargs
    ):
        return self.custom_action(
            "patch", "partial_update", request_data, user, content_type, **kwargs
        )

    def destroy(self, request_data=None, user=None, content_type="json", **kwargs):
        return self.custom_action(
            "delete", "destroy", request_data, user, content_type, **kwargs
        )

    def custom_action(
        self,
        action,
        method,
        request_data=None,
        user=None,
        content_type="json",
        **kwargs,
    ):
        request = self.__create_request(action, request_data, content_type, user)

        return self.tested_view_class.as_view({action: method})(request, **kwargs)

    def __create_request(self, method, data=None, content_type=None, user=None):
        request = None

        if "post" == method:
            request = self.client.post("", data=data, format=content_type)
        elif "get" == method:
            request = self.client.get("", data=data, format=content_type)
        elif "put" == method:
            request = self.client.put("", data=data, format=content_type)
        elif "patch" == method:
            request = self.client.patch("", data=data, format=content_type)
        elif "delete" == method:
            request = self.client.delete("", data=data, format=content_type)

        if user:
            force_authenticate(request, user=user, token=None)

        return request


def create_test_user(**kwargs):
    test_data = {
        "email": "testuser@shortage.global",
        "password": "Password123$",
        **kwargs,
    }

    user = get_user_model().objects.create_user(**test_data)

    return user


def create_test_organization(**kwargs):
    assert "owner" in kwargs, "'create_test_organization' was called without 'owner'"

    test_data = {
        "owner": None,
        "name": "TestName",
        "slug": "test_organization",
        "requested_goods": "very needed goods",
        "mission_description": "TestName helps people",
        "url": "https://www.579f9ed2-b0a7-11ed-afa1-0242ac120002.com",
        "ein_number": "91-1144442",
        "is_verified": True,
        "is_draft": False,
        **kwargs,
    }

    organization = Organization(**test_data)
    organization.save()
    return organization


def create_test_product(**kwargs):
    assert (
        "organization" in kwargs
    ), "'create_test_product' was called without 'organization'"

    test_data = {
        "organization": None,
        "name": "Test Product",
        "slug": "test_product",
        "category": "VITAL_GOODS",
        "price": 999,
        "requested_amount": 20,
        "top_priority": False,
        "position": 1,
        **kwargs,
    }

    product = Product(**test_data)
    product.save()
    return product


def create_test_instruction(**kwargs):
    assert (
        "organization" in kwargs
    ), "'create_test_instruction' was called without 'organization'"

    test_data = {
        "organization": None,
        "name": "Test Instruction",
        "address_line1": "69 Some Street",
        "city": "Springfield",
        "state_province_region": "California",
        "zip": "98765",
        **kwargs,
    }

    instruction = Instruction(**test_data)
    instruction.save()
    return instruction


def create_test_package(product, **kwargs):
    test_data = {
        "owner": None,
        "type": "SENT_BY_DONOR",
        "email": "testuser@shortage.global",
        "need_tax_deduction": False,
        "organization": None,
        **kwargs,
    }
    package = Package.objects.create(**test_data)
    PackageItem.objects.create(
        package=package,
        product=product,
        quantity=1,
        price=product.price,
        name=product.name,
        category=product.category,
        photo=product.photo,
        description=product.description,
    )
    return package


def create_test_image(
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
