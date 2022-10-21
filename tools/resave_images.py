# we need to resave images after loosing thumbnails source data and metadata

from shortage.apps.catalog.models import Organization, Product


def resave_images():
    orgs = Organization.objects.all()
    for org in orgs:
        print(">>> Resaving images for organization: %s" % org.name)

        filename = org.logo.name.split("/")[-1]
        org.logo.save(filename, org.logo.file)
        print("resaved logo: %s" % filename)

        filename = org.banner.name.split("/")[-1]
        org.banner.save(filename, org.banner.file)
        print("resaved banner: %s" % filename)

    products = Product.objects.all()
    for product in products:
        print(">>> Resaving images for product: %s" % product.name)

        filename = product.photo.name.split("/")[-1]
        product.photo.save(filename, product.photo.file)
        print("resaved photo: %s" % filename)
