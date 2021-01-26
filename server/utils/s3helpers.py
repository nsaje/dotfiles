import hashlib
import io
import json
import os
from functools import partial

import boto
from boto.s3.key import Key
from django.conf import settings

import utils.threads

DEFAULT_METADATA_SERVICE_NUM_ATTEMPTS = 10
DEFAULT_METADATA_SERVICE_TIMEOUT = 5.0


class TimeoutException(Exception):
    pass


class S3Helper(object):
    """Handles connection to S3 as well as put and get actions.
    In case S3 is not used, it falls back to local file system.
    """

    def __init__(self, bucket_name):
        self.use_s3 = settings.USE_S3 and not settings.TESTING
        if self.use_s3:
            _ensure_boto_defaults()
            self.bucket = boto.connect_s3().get_bucket(bucket_name)

    def get(self, key):
        if self.use_s3:
            k = Key(self.bucket)
            k.key = key
            return k.get_contents_as_string()

        if settings.S3_MOCK_DIR:
            with open(os.path.join(settings.S3_MOCK_DIR, os.path.basename(key)), "rb") as f:
                return f.read()

    def open_keys_async(self, keys):
        keys = list(keys)

        t = utils.threads.AsyncFunction(partial(self._download_file, keys[0]))
        t.start()

        def _get_result(t):
            result = t.join_and_get_result(timeout=600)
            if t.is_alive():
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

    def move(self, frm, to):
        if self.use_s3:
            k = self.bucket.new_key(frm)
            k.copy(self.bucket, to)
            k.delete()

        elif settings.S3_MOCK_DIR:
            os.rename(self._local_file_name(frm), self._local_file_name(to))

    def delete(self, key):
        if self.use_s3:
            k = self.bucket.new_key(key)
            k.delete()

        elif settings.S3_MOCK_DIR:
            os.remove(self._local_file_name(key))

    def _local_file_name(self, key):
        return os.path.join(settings.S3_MOCK_DIR, os.path.basename(key))

    def put(self, key, contents, human_readable_filename=None):
        try:
            contents = contents.encode("utf-8")
        except AttributeError:
            pass
        if self.use_s3:
            k = self.bucket.new_key(key)

            if human_readable_filename:
                k.set_metadata("Content-Disposition", "attachment; filename={}".format(human_readable_filename))

            k.set_contents_from_string(contents)

        elif settings.S3_MOCK_DIR:
            with open(self._local_file_name(key), "wb+") as f:
                f.write(contents)

    def put_file(self, key, source, human_readable_filename=None):
        if self.use_s3:
            k = self.bucket.new_key(key)

            if human_readable_filename:
                k.set_metadata("Content-Disposition", "attachment; filename={}".format(human_readable_filename))

            k.set_contents_from_file(source)

        elif settings.S3_MOCK_DIR:
            with open(self._local_file_name(key), "wb+") as f:
                _copy_file(source, f)

    def put_multipart(self, key, human_readable_filename=None):
        if self.use_s3:
            metadata = {}
            if human_readable_filename:
                metadata["Content-Disposition"] = "attachment; filename={}".format(human_readable_filename)

            return self.bucket.initiate_multipart_upload(key, metadata=metadata)
        else:
            return FakeMultiPartUpload(key)

    def list(self, prefix, delimiter=""):
        if self.use_s3:
            return self.bucket.list(prefix=prefix, delimiter=delimiter)
        elif settings.S3_MOCK_DIR:
            try:
                return [name for name in os.listdir(prefix) if os.path.isdir(os.path.join(prefix, name))]
            except OSError:
                return []
        return []

    def list_manifest(self, manifest_path):
        if self.use_s3:
            manifest = json.loads(self.get(manifest_path))
            for entry in manifest["entries"]:
                yield entry["url"].lstrip("s3://%s/" % self.bucket.name)

    def generate_url(self, key):
        if self.use_s3:
            k = Key(self.bucket)
            k.key = key
            return k.generate_url(3600)

        if settings.S3_MOCK_DIR:
            return "file://" + os.path.join(settings.S3_MOCK_DIR, os.path.basename(key))


class FakeMultiPartUpload(object):
    def __init__(self, key):
        self.key = key
        self.last_num = 0
        if settings.S3_MOCK_DIR:
            open(self._get_file(), "wb").close()

    def _get_file(self):
        return os.path.join(settings.S3_MOCK_DIR, os.path.basename(self.key))

    def cancel_upload(self):
        if settings.S3_MOCK_DIR:
            os.remove(self._get_file())

    def complete_upload(self):
        pass

    def upload_part_from_file(self, source, part_num):
        if part_num != self.last_num + 1:
            raise Exception("Only sequential uploads supported, expected part_num: %d" % self.last_num + 1)
        self.last_num = part_num
        if settings.S3_MOCK_DIR:
            with open(self._get_file(), "ab+") as f:
                _copy_file(source, f)


def _copy_file(source, dest):
    while 1:
        copy_buffer = source.read(1024 * 1024)
        if not copy_buffer:
            break
        dest.write(copy_buffer)


def generate_safe_filename(filename, content):
    filename = filename.lower().replace(" ", "_")
    basefnm, extension = os.path.splitext(filename)
    digest = hashlib.md5(content).hexdigest() + str(len(content))

    return basefnm + "_" + digest + extension


def get_credentials_string():
    if settings.TESTING:
        return "aws_access_key_id=bar;aws_secret_access_key=foo"
    if not settings.USE_S3:
        return ""

    _ensure_boto_defaults()
    s3_client = boto.s3.connect_to_region("us-east-1")

    access_key = s3_client.aws_access_key_id
    access_secret = s3_client.aws_secret_access_key

    security_token_param = ""
    if s3_client.provider.security_token:
        security_token_param = ";token=%s" % s3_client.provider.security_token

    return "aws_access_key_id=%s;aws_secret_access_key=%s%s" % (access_key, access_secret, security_token_param)


def _ensure_boto_defaults():
    if not boto.config._parser.has_section("Boto"):
        boto.config._parser.add_section("Boto")

    if not boto.config._parser.has_option("Boto", "metadata_service_num_attempts"):
        boto.config._parser.set("Boto", "metadata_service_num_attempts", str(DEFAULT_METADATA_SERVICE_NUM_ATTEMPTS))

    if not boto.config._parser.has_option("Boto", "metadata_service_timeout"):
        boto.config._parser.set("Boto", "metadata_service_timeout", str(DEFAULT_METADATA_SERVICE_TIMEOUT))
