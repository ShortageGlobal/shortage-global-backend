import os
from django.core.files.storage import get_storage_class
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
	bucket_name = os.getenv('SPACE_NAME', '')
	location = 'static'

class MediaStorage(S3Boto3Storage):
	bucket_name = os.getenv('SPACE_NAME', '')
	location = 'media'