import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings


def clean_url(raw_url):
    """
    Removes all utm_* and z1_* params, then alphabetically order the remaining params
    """
    if isinstance(raw_url, str):
        raw_url = raw_url.encode("utf-8")

    split_url = list(urllib.parse.urlsplit(raw_url))
    query_parameters = urllib.parse.parse_qsl(split_url[3], keep_blank_values=True)

    cleaned_query_parameters = [
        attr_value
        for attr_value in query_parameters
        if not (attr_value[0].startswith("utm_") or attr_value[0].startswith("_z1_"))
    ]

    split_url[3] = urllib.parse.urlencode(sorted(cleaned_query_parameters, key=lambda x: x[0]))

    return urllib.parse.urlunsplit(split_url), dict(query_parameters)


def combine_tracking_codes(*args):
    return "&".join([arg for arg in args if arg])


def get_full_z1_url(partial_url):
    """Returns partial_url prepended with base URL (domain)
    """
    return urllib.parse.urljoin(settings.BASE_URL, partial_url)
