from collections import defaultdict
import datetime
import itertools
import logging
import math
from multiprocessing.pool import ThreadPool


import dash.models
import reports.update

from utils import redirector_helper
from utils import statsd_helper
from utils import dates_helper

logger = logging.getLogger(__name__)

ADDITIONAL_SYNC_HOURS = 4

NUM_THREADS = 20

# If an account content (campaigns, pixies etc.) was moved,
# it should be mapped in this dictionary
MOVED_PIXIES = {  # (new-account-id, slug) : (old-account-id, slug)
    (247, 'centurylinkconversionpixel'): (119, 'centurylinkconversionpixel'),
    (247, 'centurylinklandingpages'): (119, 'centurylinklandingpages'),
    (249, 'perforceconversionpixel'): (119, 'perforceconversionpixel'),
    (249, 'perforcelandingpages'): (119, 'perforcelandingpages'),
}
MOVED_PIXIES_INVERTED = {v: k for k, v in MOVED_PIXIES.iteritems()}

# If a pixie was misplaced or for some other reason needs some of its data ignored,
# it should be specified in a BAD_PIXIE_X map.
BAD_PIXIES_ACCOUNT_LEVEL = {  # (account_id, slug): [(range_start_dt, range_end_dt),...]

}

BAD_PIXIES_AD_GROUP_LEVEL = {  # (ad_group_id, slug): [(range_start_dt, range_end_dt),...]
    (1411, 'msftdynamics'): [
        (datetime.datetime.min, datetime.datetime(2016, 1, 16, 0, 0, 0))
    ],
    (1412, 'msftdynamics'): [
        (datetime.datetime.min, datetime.datetime(2016, 1, 16, 0, 0, 0))
    ]
}


def _get_dates_to_sync(conversion_pixels):
    pairs = []
    for conversion_pixel in conversion_pixels:
        if conversion_pixel.last_sync_dt is None:
            pairs.append((dates_helper.local_today(), conversion_pixel))
            continue

        last_sync_dt = conversion_pixel.last_sync_dt - datetime.timedelta(hours=ADDITIONAL_SYNC_HOURS)
        dates = [dates_helper.utc_datetime_to_local_date(last_sync_dt)]
        while dates[-1] < dates_helper.local_today():
            dates.append(dates[-1] + datetime.timedelta(days=1))
        pairs.extend(itertools.product(dates, [conversion_pixel]))
    return pairs


@statsd_helper.statsd_timer('convapi', 'update_touchpoint_conversions_full')
def update_touchpoint_conversions_full():
    conversion_pixels = dash.models.ConversionPixel.objects.filter(archived=False)
    date_cp_pairs = _get_dates_to_sync(conversion_pixels)

    try:
        update_touchpoint_conversions(date_cp_pairs)
    except Exception:
        logger.exception('exception updating touchpoint conversions')
        return

    # all missing dates are guaranteed to be synced so last sync dt can be updated
    conversion_pixels.update(last_sync_dt=datetime.datetime.utcnow())


def _update_touchpoint_conversions_date(date_cp_tup):
    date, conversion_pixel = date_cp_tup

    logger.info('Fetching touchpoint conversions for date %s, account id %s and conversion pixel slug %s.', date,
                conversion_pixel.account_id, conversion_pixel.slug)
    pixie = (conversion_pixel.account_id, conversion_pixel.slug, )
    if pixie in MOVED_PIXIES:
        redirects_impressions = redirector_helper.fetch_redirects_impressions(
            date,
            MOVED_PIXIES[pixie][0],
            MOVED_PIXIES[pixie][1],
        )
        reports.update.update_touchpoint_conversions(
            date,
            conversion_pixel.account_id,
            conversion_pixel.slug,
            process_touchpoint_conversions(redirects_impressions)
        )
    redirects_impressions = redirector_helper.fetch_redirects_impressions(
        date,
        conversion_pixel.account_id,
        conversion_pixel.slug
    )
    reports.update.update_touchpoint_conversions(
        date,
        conversion_pixel.account_id,
        conversion_pixel.slug,
        process_touchpoint_conversions(redirects_impressions)
    )


@statsd_helper.statsd_timer('convapi', 'update_touchpoint_conversions')
def update_touchpoint_conversions(date_cp_pairs):
    pool = ThreadPool(processes=NUM_THREADS)
    result = pool.map_async(_update_touchpoint_conversions_date, date_cp_pairs)
    pool.close()
    pool.join()

    result.get()  # raises an exception if one of the workers raised one


@statsd_helper.statsd_timer('convapi', 'process_touchpoint_conversions')
def process_touchpoint_conversions(redirects_impressions):
    '''
    Processes click and pixel impression data fetched from r1 and return valid touchpoint-conversion pairs.
    Input:
        {
            zuid: [
                (redirect, pixel_impression), ...
            ]
        }
    Redirector returns pairs of redirects and pixel impressions joined by zuid (we get every pair where zuid matches).
    It returns only those pairs that are equal to or less than 90 (max conversion window) days apart.

    Output:
    Valid touchpoint-conversion pairs in a list. A conversion is valid when:
        - zuid matches
        - click occurred on a content ad belonging to a campaign with a tracking pixel set up,
          and that pixel's slug matches conversion slug
        - no other conversion matching these criteria happened between the click and conversion
    '''
    touchpoint_conversions = []
    for zuid, zuid_redirects_impressions in redirects_impressions.iteritems():
        touchpoint_conversion_dict = defaultdict(dict)
        for redirect_impression in zuid_redirects_impressions:
            slug, account_id = MOVED_PIXIES_INVERTED.get(
                (redirect_impression['slug'], redirect_impression['accountId']),
                (redirect_impression['slug'], redirect_impression['accountId']),
            )

            ad_group_id = redirect_impression['adGroupId']
            content_ad_id = redirect_impression['contentAdId']
            conversion_key = (account_id, slug)
            source_slug = redirect_impression['source']
            ad_lookup = redirect_impression.get('adLookup', False)

            redirect_id = redirect_impression['redirectId']
            redirect_ts = datetime.datetime.strptime(redirect_impression['redirectTimestamp'], '%Y-%m-%dT%H:%M:%SZ')

            impression_id = redirect_impression['impressionId']
            impression_ts = datetime.datetime.strptime(redirect_impression['impressionTimestamp'], '%Y-%m-%dT%H:%M:%SZ')

            if content_ad_id == 0:  # legacy simple redirect
                continue

            if ad_lookup:
                continue

            if source_slug == 'z1':  # source slug from dashboard visits
                continue

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

            if pixel.archived:
                statsd_helper.statsd_incr('convapi.process.skip_archived_pixel')
                continue

            try:
                ca = dash.models.ContentAd.objects.select_related('ad_group__campaign').get(id=content_ad_id)
            except dash.models.ContentAd.DoesNotExist:
                logger.warning('Unknown content ad. content_ad_id=%s ad_group_id=%s source=%s',
                               content_ad_id, ad_group_id, source_slug)
                continue

            try:
                source = dash.models.Source.objects.get(tracking_slug=source_slug)
            except dash.models.Source.DoesNotExist:
                logger.warning('Unknown source slug. source=%s', source_slug)
                continue

            if ca.ad_group.campaign.account_id != pixel.account_id:
                continue

            potential_touchpoint_conversion = {
                'zuid': zuid,
                'slug': slug,
                'date': dates_helper.utc_datetime_to_local_date(impression_ts),
                'conversion_id': impression_id,
                'conversion_timestamp': impression_ts,
                'account_id': account_id,
                'campaign_id': ca.ad_group.campaign_id,
                'ad_group_id': ca.ad_group_id,
                'content_ad_id': content_ad_id,
                'touchpoint_id': redirect_id,
                'source_id': source.id,
                'touchpoint_timestamp': redirect_ts,
                'conversion_lag': int(math.ceil((impression_ts - redirect_ts).total_seconds() / (60 * 60)))
            }

            if _touchpoint_conversion_falls_within_bad_pixie_range(account_id, potential_touchpoint_conversion):
                continue

            touchpoint_conversion_dict[redirect_id][conversion_key] = potential_touchpoint_conversion

        for touchpoint in touchpoint_conversion_dict.itervalues():
            touchpoint_conversions.extend(touchpoint.itervalues())

    return touchpoint_conversions


def _touchpoint_conversion_falls_within_bad_pixie_range(account_id, touchpoint_conversion):
    ad_group_id = touchpoint_conversion['ad_group_id']
    slug = touchpoint_conversion['slug']
    conversion_timestamp = touchpoint_conversion['conversion_timestamp']

    if (account_id, slug) in BAD_PIXIES_ACCOUNT_LEVEL:
        for range_start_dt, range_end_dt in BAD_PIXIES_ACCOUNT_LEVEL[(account_id, slug)]:
            if range_start_dt <= conversion_timestamp <= range_end_dt:
                return True

    if (ad_group_id, slug) in BAD_PIXIES_AD_GROUP_LEVEL:
        for range_start_dt, range_end_dt in BAD_PIXIES_AD_GROUP_LEVEL[(ad_group_id, slug)]:
            if range_start_dt <= conversion_timestamp <= range_end_dt:
                return True

    return False
