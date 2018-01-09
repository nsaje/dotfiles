import os
import io
import hashlib
from functools import partial

import json
import boto
from boto.s3.key import Key

import utils.threads
from django.conf import settings


class TimeoutException(Exception):
    pass


class S3Helper(object):
    """Handles connection to S3 as well as put and get actions.
    In case S3 is not used, it falls back to local file system.
    """

    def __init__(self, bucket_name=settings.S3_BUCKET):
        if settings.USE_S3:
            self.bucket = boto.connect_s3(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            ).get_bucket(bucket_name)

    def get(self, key):
        if settings.USE_S3:
            k = Key(self.bucket)
            k.key = key
            return k.get_contents_as_string()

        if settings.FILE_STORAGE_DIR:
            with open(os.path.join(settings.FILE_STORAGE_DIR, os.path.basename(key)), 'r') as f:
                return f.read()

    def open_keys_async(self, keys):
        keys = list(keys)

        t = utils.threads.AsyncFunction(partial(self._download_file, keys[0]))
        t.start()

        def _get_result(t):
            result = t.join_and_get_result(timeout=600)
            if t.isAlive():
                raise TimeoutException("Downloading file from S3 taking too long")
            return result

        for key in keys[1:]:
            result = _get_result(t)
            t = utils.threads.AsyncFunction(partial(self._download_file, key))
            t.start()
            yield result
        yield _get_result(t)

    def _download_file(self, key):
        k = Key(self.bucket)
        k.key = key
        f = io.BytesIO()
        k.get_contents_to_file(f)
        f.seek(0)
        return f

    def put(self, key, contents, human_readable_filename=None):
        if settings.USE_S3:
            k = self.bucket.new_key(key)

            if human_readable_filename:
                k.set_metadata('Content-Disposition', 'attachment; filename={}'.format(human_readable_filename))

            k.set_contents_from_string(contents)

        elif settings.FILE_STORAGE_DIR:
            with open(os.path.join(settings.FILE_STORAGE_DIR, os.path.basename(key)), 'w+') as f:
                f.write(contents)

    def put_file(self, key, source, human_readable_filename=None):
        if settings.USE_S3:
            k = self.bucket.new_key(key)

            if human_readable_filename:
                k.set_metadata('Content-Disposition', 'attachment; filename={}'.format(human_readable_filename))

            k.set_contents_from_file(source)

        elif settings.FILE_STORAGE_DIR:
            with open(os.path.join(settings.FILE_STORAGE_DIR, os.path.basename(key)), 'w+') as f:
                _copy_file(source, f)

    def put_multipart(self, key, human_readable_filename=None):
        if settings.USE_S3:
            metadata = {}
            if human_readable_filename:
                metadata['Content-Disposition'] = 'attachment; filename={}'.format(human_readable_filename)

            return self.bucket.initiate_multipart_upload(key, metadata=metadata)
        else:
            return FakeMultiPartUpload(key)

    def list(self, prefix):
        if settings.USE_S3:
            return self.bucket.list(prefix=prefix)
        elif settings.FILE_STORAGE_DIR:
            try:
                return [name for name in os.listdir(prefix) if os.path.isdir(os.path.join(prefix, name))]
            except OSError:
                return []
        return []

    def list_manifest(self, manifest_path):
        if settings.USE_S3:
            manifest = json.loads(self.get(manifest_path))
            for entry in manifest['entries']:
                yield entry['url'].lstrip('s3://%s/' % self.bucket.name)


class FakeMultiPartUpload(object):
    def __init__(self, key):
        self.key = key
        self.last_num = 0
        if settings.FILE_STORAGE_DIR:
            open(self._get_file(), 'w').close()

    def _get_file(self):
        return os.path.join(settings.FILE_STORAGE_DIR, os.path.basename(self.key))

    def cancel_upload(self):
        if settings.FILE_STORAGE_DIR:
            os.remove(self._get_file())

    def complete_upload(self):
        pass

    def upload_part_from_file(self, source, part_num):
        if part_num != self.last_num + 1:
            raise Exception("Only sequential uploads supported, expected part_num: %d" % self.last_num + 1)
        self.last_num = part_num
        if settings.FILE_STORAGE_DIR:
            with open(self._get_file(), 'a+') as f:
                _copy_file(source, f)


def _copy_file(source, dest):
    while 1:
        copy_buffer = source.read(1024 * 1024)
        if not copy_buffer:
            break
        dest.write(copy_buffer)


def generate_safe_filename(filename, content):
    filename = filename.lower().replace(' ', '_')
    basefnm, extension = os.path.splitext(filename)
    digest = hashlib.md5(content).hexdigest() + str(len(content))

    return basefnm + '_' + digest + extension
