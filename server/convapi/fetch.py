from collections import defaultdict
import datetime

import dash.models
from utils import redirector_helper

MAX_CONVERSION_WINDOW_DAYS = 90


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
        touchpoints = sorted(obj['touchpoints'], key=lambda x: x['timestamp'])
        impressions = sorted(obj['impressions'], key=lambda x: x['timestamp'])

        tp_start_ix_by_slug = defaultdict(int)
        for imp in impressions:
            potential_impression_touchpoints = []

            end_reached = True
            tp_start_ix = tp_start_ix_by_slug[(imp['account_id'], imp['slug'])]
            for tp_ix, tp in enumerate(touchpoints[tp_start_ix:]):
                if tp['timestamp'] > imp['timestamp']:
                    # potential touchpoints for next impression start from here
                    tp_start_ix_by_slug[(imp['account_id'], imp['slug'])] = tp_ix
                    end_reached = False
                    break

                potential_impression_touchpoints.append(tp)

            if end_reached:
                # current impression appears later than every touchpoint
                # subsequent impressions with same (account, slug) should have no potential touchpoints
                tp_start_ix_by_slug[(imp['account_id'], imp['slug'])] = len(touchpoints)

            touchpoint_conversion_pairs.extend(
                _get_touchpoint_conversion_pairs(imp, potential_impression_touchpoints)
            )

    return touchpoint_conversion_pairs
