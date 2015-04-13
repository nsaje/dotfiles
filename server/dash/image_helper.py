import json
import urllib2

from django.conf import settings


class ImageProcessingException(Exception):
    pass


def process_image(url, crop_areas):
    if not url:
        return None, 0, 0

    payload = {'image_url': url}

    crops_dict = _get_crops_dict(crop_areas)
    if crops_dict is not None:
        payload['crops'] = crops_dict

    data = json.dumps(payload)

    try:
        response = urllib2.urlopen(settings.Z3_API_IMAGE_URL, data)
    except urllib2.HTTPError as e:
        raise ImageProcessingException(e)

    if response.code != 200:
        raise ImageProcessingException()

    result = json.loads(response.read())

    status = result.get('status')
    image_id = result.get('key')
    width = result.get('width')
    height = result.get('height')
    image_hash = result.get('imagehash')

    if status is None or status != 'success' or\
       image_id is None or width is None or height is None:
        raise ImageProcessingException()

    return image_id, width, height, image_hash


def _get_crops_dict(crop_areas):
    if crop_areas is None:
        return

    return {
        'square': {
            'tl': {
                'x': crop_areas[0][0][0],
                'y': crop_areas[0][0][1]
            },
            'br': {
                'x': crop_areas[0][1][0],
                'y': crop_areas[0][1][1]
            }
        },
        'landscape': {
            'tl': {
                'x': crop_areas[1][0][0],
                'y': crop_areas[1][0][1]
            },
            'br': {
                'x': crop_areas[1][1][0],
                'y': crop_areas[1][1][1]
            }
        }
    }
