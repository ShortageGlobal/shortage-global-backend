from django.contrib.auth import get_user_model
from shortage.apps.catalog.models import Organization, Product
from shortage.apps.packages.models import Package, PackageItem


def create_test_user(**kwargs):
    test_data = {
        "email": "testuser@shortage.global",
        "password": "12345",
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


def create_test_package(product, **kwargs):
    test_data = {
        "owner": None,
        "type": "SENT_BY_DONOR",
        "email": "testuser@shortage.global",
        "need_tax_deduction": False,
        **kwargs,
    }
    package = Package.objects.create(**test_data)
    PackageItem.objects.create(package=package, product=product, quantity=1)
    return package
