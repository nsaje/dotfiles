import os
import hashlib

import boto
from boto.s3.key import Key

from django.conf import settings


class S3Helper(object):
    """Handles connection to S3 as well as put and get actions.
    In case S3 is not used, it falls back to local file system.
    """

    def __init__(self):
        if settings.USE_S3:
            self.bucket = boto.connect_s3(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            ).get_bucket(settings.S3_BUCKET)

    def get(self, key):
        if settings.USE_S3:
            k = Key(self.bucket)
            k.key = key
            return k.get_contents_as_string()

        if len(settings.FILE_STORAGE_DIR):
            with open(os.path.join(settings.FILE_STORAGE_DIR, os.path.basename(key)), 'r') as f:
                return f.read()

    def put(self, key, contents):
        if settings.USE_S3:
            k = self.bucket.new_key(key)
            k.set_contents_from_string(contents)

        elif len(settings.FILE_STORAGE_DIR):
            with open(os.path.join(settings.FILE_STORAGE_DIR, os.path.basename(key)), 'w+') as f:
                f.write(contents)


def generate_safe_filename(filename, content):
    filename = filename.lower().replace(' ', '_')
    basefnm, extension = os.path.splitext(filename)
    digest = hashlib.md5(content).hexdigest() + str(len(content))

    return basefnm + '_' + digest + extension
