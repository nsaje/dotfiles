import urlparse

from django.conf import settings


def get_image_url(image_id, width, height, crop):
    if image_id is None or width is None or height is None or crop is None:
        return None

    path = '/{}.jpg?w={}&h={}&fit=crop&crop={}&fm=jpg'.format(
        image_id, width, height, crop)
    return urlparse.urljoin(settings.IMAGE_THUMBNAIL_URL, path)
