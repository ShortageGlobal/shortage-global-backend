from django.core.files.storage import get_storage_class


class MediaStorage(get_storage_class()):
    bucket_name = 'shortage-media'
    querystring_auth = False
