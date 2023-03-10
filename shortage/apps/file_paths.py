import uuid
import os


def get_uuid_path(directory, filename):
    ext = filename.split(".")[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)

    return os.path.join(directory, filename)


def get_organization_path(instance, filename):
    return get_uuid_path(f"photo/organization/{str(instance.pk)}/", filename)


def get_external_organization_path(instance, filename):
    return get_uuid_path(f"photo/external_organizations/", filename)


def get_product_path(instance, filename):
    return get_uuid_path(f"photo/product/{str(instance.pk)}/", filename)


def get_package_path(instance, filename):
    return get_uuid_path(f"photo/package/", filename)


def get_tax_deduction_receipt_path(instance, filename):
    return get_uuid_path(
        f"photo/package/tax_deduction_receipt/{instance.uuid}/", filename
    )


def get_corporate_donation_path(instance, filename):
    return get_uuid_path(f"photo/corporate_donations/", filename)


def get_blog_post_content_uploads_path(user, filename):
    return get_uuid_path(f"blog/content_uploads/{user}", filename)


def get_blog_post_photo_path(instance, filename):
    return get_uuid_path(f"blog/previews/{instance.author.pk}/", filename)
