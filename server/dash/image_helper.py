import httplib
import json
import urllib2

from django.conf import settings


NUM_RETRIES = 3


class ImageProcessingException(Exception):

    def __init__(self, message="", status=None):
        Exception.__init__(self, message)
        self._status = status

    def status(self):
        return self._status


def process_image(url, crop_areas):
    if not url:
        return None, 0, 0

    payload = {'image_url': url}

    crops_dict = _get_crops_dict(crop_areas)
    if crops_dict is not None:
        payload['crops'] = crops_dict

    payload_json = json.dumps(payload)

    for _ in xrange(NUM_RETRIES):
        try:
            return _attempt_process_image(payload_json)
        except Exception as error:
            pass

    raise error


def _attempt_process_image(payload_json):
    response_code = httplib.INTERNAL_SERVER_ERROR

    try:
        response = urllib2.urlopen(settings.Z3_API_IMAGE_URL, payload_json)
        response_code = response.code
    except urllib2.HTTPError, error:
        try:
            error_dict = json.loads(error.read())
        except:
            raise ImageProcessingException()

        if error.code == httplib.INTERNAL_SERVER_ERROR:
            raise ImageProcessingException(status=error_dict.get('status'))
        else:
            raise ImageProcessingException(error)

    if response_code != httplib.OK:
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
