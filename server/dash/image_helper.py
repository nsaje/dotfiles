import os
import urllib.parse
import time
import random

from django.conf import settings

from utils import s3helpers

UPLOADED_IMAGE_KEY_FMT = 'u/{batch_id}/{ts}{rand}{ext}'


def get_image_url(image_id, width, height, crop):
    if image_id is None or width is None or height is None or crop is None:
        return None

    path = '/{}.jpg?w={}&h={}&fit=crop&crop={}&fm=jpg'.format(
        image_id, width, height, crop)
    return urllib.parse.urljoin(settings.IMAGE_THUMBNAIL_URL, path)


def upload_image_to_s3(image, batch_id):
    if not batch_id:
        raise Exception('Missing batch id')

    key = UPLOADED_IMAGE_KEY_FMT.format(
        batch_id=batch_id,
        ts=int(time.time() * 1000),
        rand=random.randint(10000, 99999),
        ext=os.path.splitext(image.name)[1],
    )

    s3helpers.S3Helper(settings.S3_BUCKET_THUMBNAILER).put(key, image.read())
    return urllib.parse.urljoin(settings.IMAGE_THUMBNAIL_URL, key)
