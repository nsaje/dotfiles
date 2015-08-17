import urlparse
import urllib


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


def get_ad_group_tracking_codes(user_tracking_codes, tracking_ids, enable_ga_tracking):
    tracking_codes = [user_tracking_codes]
    if enable_ga_tracking:
        tracking_codes.append(tracking_ids)
    return tracking_codes


def add_tracking_codes_to_url(url, tracking_codes):
    if not tracking_codes:
        return url

    parsed = list(urlparse.urlparse(url))

    parts = []
    if parsed[4]:
        parts.append(parsed[4])
    parts.append(tracking_codes)

    parsed[4] = '&'.join(parts)

    return urlparse.urlunparse(parsed)


def get_tracking_id_params(ad_group_id, tracking_slug):
    tracking_codes = '_z1_adgid=%s' % (ad_group_id)

    if tracking_slug is not None:
        tracking_codes += '&_z1_msid=%s' % (tracking_slug)

    return tracking_codes
