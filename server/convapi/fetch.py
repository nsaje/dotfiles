import datetime

import dash.models
from utils import redirector_helper

MAX_CONVERSION_WINDOW_DAYS = 90
MIN_DELAY_BETWEEN_CONVERSIONS_MINS = 10


def _get_touchpoint_conversion_pairs(impression, potential_touchpoints):
    try:
        pixel = dash.models.ConversionPixel.objects.get(slug=impression['slug'], account_id=impression['account_id'])
    except dash.models.ConversionPixel.DoesNotExist:
        return []

    pairs = []
    for tp in potential_touchpoints:
        try:
            ca = dash.models.ContentAd.objects.select_related('ad_group__campaign').get(id=tp['creative_id'])
        except dash.models.ContentAd.DoesNotExist:
            continue

        if pixel not in ca.ad_group.campaign.conversion_pixels.all():
            continue

        if impression['timestamp'] - tp['timestamp'] > datetime.timedelta(days=MAX_CONVERSION_WINDOW_DAYS):
            continue

        pairs.append((impression, tp))

    return pairs


def fetch_touchpoints_impressions(date):
    touchpoints_impressions = redirector_helper.fetch_touchpoints_impressions(date)

    touchpoint_conversion_pairs = []
    for obj in touchpoints_impressions.itervalues():
        impressions = sorted(obj['impressions'], key=lambda x: x['timestamp'])

        latest_impression_ts_by_slug = {}
        for imp in impressions:
            dict_key = (imp['account_id'], imp['slug'])
            if dict_key not in latest_impression_ts_by_slug:
                latest_impression_ts_by_slug[dict_key] = datetime.datetime.min

            latest_impression_ts = latest_impression_ts_by_slug[dict_key]
            if imp['timestamp'] - latest_impression_ts < datetime.timedelta(minutes=MIN_DELAY_BETWEEN_CONVERSIONS_MINS):
                # TODO: suggested by andraz, discuss with product
                continue

            potential_impression_touchpoints = [tp for tp in obj['touchpoints'] if
                                                tp['timestamp'] > latest_impression_ts and
                                                tp['timestamp'] < imp['timestamp']]

            latest_impression_ts_by_slug[dict_key] = imp['timestamp']
            touchpoint_conversion_pairs.extend(
                _get_touchpoint_conversion_pairs(imp, potential_impression_touchpoints)
            )

    return touchpoint_conversion_pairs
