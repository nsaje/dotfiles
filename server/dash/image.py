import json
import urllib2

from django.conf import settings


def process_image(url, crop_areas):
    if not url:
        return

    payload = {'image-url': url}

    crops_dict = _get_crops_dict(crop_areas)
    if crops_dict is not None:
        payload['crops'] = crops_dict

    data = json.dumps(payload)
    response = urllib2.urlopen(settings.Z3_API_URL, data)

    return json.loads(response.read())['key']


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
