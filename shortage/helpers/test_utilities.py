from shortage.apps.catalog.models import Organization, Product


def create_test_organization(owner, slug=None):
    test_data = {
        "name": "TestName",
        "slug": slug if slug else "test_slug",
        "description": "Some description",
        "url": "https://www.someurl.com",
        "ein_number": "12345",
        "owner": owner,
    }

    organization = Organization(**test_data)
    organization.is_verified = True
    organization.is_draft = False

    organization.save()

    return organization


def create_test_product(organization, slug=None):
    test_data = {
        "name": "Test Product",
        "slug": slug if slug else "test_product",
        "category": "VITAL_GOODS",
        "price": 999,
        "requested_amount": 20,
        "top_priority": False,
        "position": 1,
        "organization_id": organization.id,
    }
    product = Product(**test_data)
    product.save()

    return product
