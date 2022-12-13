# we need to resave images after loosing thumbnails source data and metadata

from shortage.apps.catalog.models import Organization, Product, OrganizationBlogPost


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

    blog_posts = OrganizationBlogPost.objects.all()
    for blog_post in blog_posts:
        print(">>> Resaving images for blog post: %s" % blog_post.title)

        if blog_post.image.name:
            filename = blog_post.image.name.split("/")[-1]
            blog_post.image.save(filename, blog_post.image.file)
            print("resaved photo: %s" % filename)
