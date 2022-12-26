from easy_thumbnails.files import get_thumbnailer


def get_thumbnail_for_image(image, name):
    if image:
        return get_thumbnailer(image)[name]

    return None
