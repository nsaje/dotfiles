import urlparse
import urllib

from django.core.urlresolvers import reverse
from django.conf import settings


def clean_url(raw_url):
    '''
    Removes all utm_* and z1_* params, then alphabetically order the remaining params
    '''
    if isinstance(raw_url, unicode):
        raw_url = raw_url.encode('utf-8')

    split_url = list(urlparse.urlsplit(raw_url))
    query_parameters = urlparse.parse_qsl(split_url[3], keep_blank_values=True)

    cleaned_query_parameters = filter(
        lambda (attr, value): not (attr.startswith('utm_') or attr.startswith('_z1_')),
        query_parameters
    )

    split_url[3] = urllib.urlencode(sorted(cleaned_query_parameters, key=lambda x: x[0]))

    return urlparse.urlunsplit(split_url), dict(query_parameters)


def combine_tracking_codes(*args):
    return '&'.join([arg for arg in args if arg])


def get_full_z1_url(partial_url):
    """Returns partial_url prepended with base URL (domain)

    Don't use this for generating zwei callback URLS -
    Use settings.ZWEI_CALLBACK_HOST instead.
    """
    return urlparse.urljoin(settings.BASE_URL, partial_url)


def get_zwei_callback_url(action_id):
    """Returns full zwei callback URL"""
    return urlparse.urljoin(
        settings.ZWEI_CALLBACK_HOST,
        reverse('api.zwei_callback', kwargs={'action_id': action_id})
    )
