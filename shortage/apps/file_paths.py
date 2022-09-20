import uuid
import os


def get_uuid_path(directory, filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)

    return os.path.join(directory, filename)


def get_organization_path(instance, filename):
    return get_uuid_path(f"photo/organization/{str(instance.slug)}/", filename)


def get_product_path(instance, filename):
    print(instance)
    return get_uuid_path(f"photo/product/{str(instance.slug)}/", filename)


def get_package_path(instance, filename):
    return get_uuid_path(f"photo/package/%Y/%m/%d/", filename)


def get_corporate_donation_path(instance, filename):
    return get_uuid_path(f"photo/corporate_donations/%Y/%m/%d/", filename)
