from django.contrib.auth import get_user_model
from shortage.apps.catalog.models import Organization, Product
from shortage.apps.packages.models import Package


def create_test_user(**kwargs):
    test_data = {
        "email": "testuser@shortage.global",
        "password": "12345",
        **kwargs,
    }
    User = get_user_model()
    user = User.objects.create_user(**test_data)
    return user


def create_test_organization(**kwargs):
    assert "owner" in kwargs, "'create_test_organization' was called without 'owner'"

    test_data = {
        "owner": None,
        "name": "TestName",
        "slug": "test_organization",
        "description": "Some description",
        "url": "https://www.someurl.com",
        "ein_number": "12345",
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


def create_test_package(**kwargs):
    assert (
        "organization" in kwargs
    ), "'create_test_package' was called without 'organization'"

    product = create_test_product(organization=kwargs.pop("organization"))

    test_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "user@email.com",
        "phone_number": "1234567890",
        "delivery_company": "Amazon",
        "tracking_code": "AZ12345678CD",
        "note": "",
        "photo": None,
    }

    package = Package(**test_data)
    package.save()
    return package
