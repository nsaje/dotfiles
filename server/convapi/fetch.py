from collections import defaultdict

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
            account_id = redirect_impression['account_id']
            content_ad_id = redirect_impression['content_ad_id']
            conversion_key = (account_id, slug)

            click_id = redirect_impression['click_id']
            click_ts = redirect_impression['click_timestamp']
            impression_ts = redirect_impression['impression_timestamp']

            if click_ts > impression_ts:
                continue

            if click_id in touchpoint_conversion_dict and\
               conversion_key in touchpoint_conversion_dict[click_id] and\
               impression_ts > touchpoint_conversion_dict[click_id][conversion_key]['impression_timestamp']:
                continue

            try:
                pixel = dash.models.ConversionPixel.objects.get(slug=slug, account_id=account_id)
            except dash.models.ConversionPixel.DoesNotExist:
                continue

            try:
                ca = dash.models.ContentAd.objects.select_related('ad_group__campaign').get(id=content_ad_id)
            except:
                continue

            if ca.ad_group.campaign.account_id != pixel.account_id:
                continue

            touchpoint_conversion_dict[click_id][conversion_key] = redirect_impression

        for touchpoint in touchpoint_conversion_dict.itervalues():
            touchpoint_conversions.extend(touchpoint.itervalues())

    return touchpoint_conversions
