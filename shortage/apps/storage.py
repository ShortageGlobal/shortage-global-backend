import os
from django.core.files.storage import get_storage_class

class StaticStorage(get_storage_class()):
	bucket_name = os.getenv('SPACE_NAME', '')
	location = 'static'

class MediaStorage(get_storage_class()):
	bucket_name = os.getenv('SPACE_NAME', '')
	location = 'media'