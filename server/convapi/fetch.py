from collections import defaultdict
import datetime

import dash.models
from utils import redirector_helper

MIN_DELAY_BETWEEN_CONVERSIONS_MINS = 10


def fetch_touchpoints_impressions(date):
    redirects_impressions = redirector_helper.fetch_redirects_impressions(date)

    touchpoint_conversions = []
    for zuid, zuid_redirects_impressions in redirects_impressions.iteritems():
        touchpoint_conversion_dict = defaultdict(dict)
        for redirect_impression in zuid_redirects_impressions:
            slug = redirect_impression['slug']
            account_id = redirect_impression['accountId']
            content_ad_id = redirect_impression['contentAdId']
            conversion_key = (account_id, slug)
            source_slug = redirect_impression['source']

            redirect_id = redirect_impression['redirectId']
            redirect_ts = datetime.datetime.strptime(redirect_impression['redirectTimestamp'], '%Y-%m-%dT%H:%M:%SZ')

            impression_id = redirect_impression['impressionId']
            impression_ts = datetime.datetime.strptime(redirect_impression['impressionTimestamp'], '%Y-%m-%dT%H:%M:%SZ')

            if redirect_ts > impression_ts:
                continue

            if redirect_id in touchpoint_conversion_dict and\
               conversion_key in touchpoint_conversion_dict[redirect_id] and\
               impression_ts > touchpoint_conversion_dict[redirect_id][conversion_key]['conversion_timestamp']:
                continue

            try:
                pixel = dash.models.ConversionPixel.objects.get(slug=slug, account_id=account_id)
            except dash.models.ConversionPixel.DoesNotExist:
                continue

            try:
                ca = dash.models.ContentAd.objects.select_related('ad_group__campaign').get(id=content_ad_id)
            except dash.models.ContentAd.DoesNotExist:
                continue

            try:
                source = dash.models.Source.objects.get(tracking_slug=source_slug)
            except dash.models.Source.DoesNotExist:
                continue

            if ca.ad_group.campaign.account_id != pixel.account_id:
                continue

            potential_touchpoint_conversion = {
                'slug': slug,
                'zuid': zuid,
                'conversion_id': impression_id,
                'conversion_timestamp': impression_ts,
                'account_id': account_id,
                'campaign_id': ca.ad_group.campaign_id,
                'ad_group_id': ca.ad_group_id,
                'content_ad_id': content_ad_id,
                'source_id': source.id,
                'touchpoint_timestamp': redirect_ts,
                'conversion_lag': (impression_ts - redirect_ts).total_seconds()
            }

            touchpoint_conversion_dict[redirect_id][conversion_key] = potential_touchpoint_conversion

        for touchpoint in touchpoint_conversion_dict.itervalues():
            touchpoint_conversions.extend(touchpoint.itervalues())

    return touchpoint_conversions
