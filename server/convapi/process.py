from collections import defaultdict
import datetime
import itertools
import logging
import math
import pytz
from multiprocessing.pool import ThreadPool

from django.db.models import Min
from django.conf import settings

import dash.models
import reports.update

from utils import redirector_helper
from utils import statsd_helper

logger = logging.getLogger(__name__)

# take ET into consideration - server time is in UTC while we query for ET dates
ADDITIONAL_SYNC_HOURS = 10

NUM_THREADS = 20


def _utc_datetime_to_est_date(dt):
    dt = dt.replace(tzinfo=pytz.utc)
    return dt.astimezone(pytz.timezone(settings.DEFAULT_TIME_ZONE)).date()


def _get_dates_to_sync(conversion_pixels):
    min_last_sync_dt = conversion_pixels.\
        filter(last_sync_dt__isnull=False).\
        aggregate(Min('last_sync_dt'))['last_sync_dt__min']

    if min_last_sync_dt is None:
        min_last_sync_dt = datetime.datetime.utcnow()

    # add a buffer so we don't miss some data
    min_last_sync_dt = min_last_sync_dt - datetime.timedelta(hours=ADDITIONAL_SYNC_HOURS)

    dates = [min_last_sync_dt.date()]
    while dates[-1] < datetime.datetime.utcnow().date():
        dates.append(dates[-1] + datetime.timedelta(days=1))

    return dates


@statsd_helper.statsd_timer('convapi', 'update_touchpoint_conversions_full')
def update_touchpoint_conversions_full():
    conversion_pixels = dash.models.ConversionPixel.objects.filter(archived=False)
    dates = _get_dates_to_sync(conversion_pixels)
    update_touchpoint_conversions(dates, conversion_pixels)

    # all missing dates are guaranteed to be synced so last sync dt can be updated
    conversion_pixels.update(last_sync_dt=datetime.datetime.utcnow())


def _update_touchpoint_conversions_date(date_cp_tup):
    date, conversion_pixel = date_cp_tup

    logger.info('Fetching touchpoint conversions for date %s, account id %s and conversion pixel slug %s.', date,
                conversion_pixel.account_id, conversion_pixel.slug)
    redirects_impressions = redirector_helper.fetch_redirects_impressions(date, conversion_pixel.account_id,
                                                                          conversion_pixel.slug)
    touchpoint_conversion_pairs = process_touchpoint_conversions(redirects_impressions)
    reports.update.update_touchpoint_conversions(date, conversion_pixel.account_id, conversion_pixel.slug,
                                                 touchpoint_conversion_pairs)


@statsd_helper.statsd_timer('convapi', 'update_touchpoint_conversions')
def update_touchpoint_conversions(dates, conversion_pixels):
    pool = ThreadPool(processes=NUM_THREADS)
    pool.map_async(_update_touchpoint_conversions_date, itertools.product(dates, conversion_pixels))
    pool.close()
    pool.join()


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
            slug = redirect_impression['slug']
            account_id = redirect_impression['accountId']
            ad_group_id = redirect_impression['adGroupId']
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

            if pixel.archived:
                statsd_helper.statsd_incr('convapi.process.skip_archived_pixel')
                continue

            try:
                ca = dash.models.ContentAd.objects.select_related('ad_group__campaign').get(id=content_ad_id)
            except dash.models.ContentAd.DoesNotExist:
                if content_ad_id != 0:
                    logger.warning('Unknown content ad. content_ad_id=%s ad_group_id=%s source=%s',
                                   content_ad_id, ad_group_id, source_slug)
                continue

            try:
                source = dash.models.Source.objects.get(tracking_slug=source_slug)
            except dash.models.Source.DoesNotExist:
                if source_slug != 'z1':
                    # source slug for visits from dashboard
                    logger.warning('Unknown source slug. source=%s', source_slug)
                continue

            if ca.ad_group.campaign.account_id != pixel.account_id:
                continue

            potential_touchpoint_conversion = {
                'zuid': zuid,
                'slug': slug,
                'date': _utc_datetime_to_est_date(impression_ts),
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

            touchpoint_conversion_dict[redirect_id][conversion_key] = potential_touchpoint_conversion

        for touchpoint in touchpoint_conversion_dict.itervalues():
            touchpoint_conversions.extend(touchpoint.itervalues())

    return touchpoint_conversions
