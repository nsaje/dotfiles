import boto

from django.conf import settings


class S3Helper(object):

    def __init__(self):
        self.initialized = False

        if settings.USE_S3:
            self.bucket = boto.connect_s3(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            ).get_bucket(settings.S3_BUCKET)
            self.initialized = True

    def put(self, key, contents):
        if self.initialized:
            k = boto.s3.Key(self.bucket)
            k.key = key

            k.set_contents_from_string(contents)
