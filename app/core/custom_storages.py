from storages.backends.s3boto3 import S3Boto3Storage

StaticS3Storage = lambda: S3Boto3Storage(location="s")  # noqa E731
MediaS3Storage = lambda: S3Boto3Storage(location="m")  # noqa E731
PhotosS3Storage = lambda: S3Boto3Storage(location="p")  # noqa E731
