from storages.backends.s3boto3 import S3Boto3Storage

StaticS3Storage = lambda: S3Boto3Storage(  # noqa E731
    location="s", bucket_name="caves.app"
)
MediaS3Storage = lambda: S3Boto3Storage(  # noqa E731
    location="m", bucket_name="caves.app"
)
PhotosS3Storage = lambda: S3Boto3Storage(  # noqa E731
    location="p", bucket_name="caves.app"
)
