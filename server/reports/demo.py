from dateutil import rrule
import logging

from slugify import slugify

from utils.statsd_helper import statsd_incr
import dash.models
import reports.api
import reports.update
import reports.models
from reports.models import TRAFFIC_METRICS, POSTCLICK_METRICS, CONVERSION_METRICS

logger = logging.getLogger(__name__)

def refresh_demo_data(start_date, end_date):
    try:
        ad_map, source_map = _copy_content_ads()
        _refresh_stats_data(start_date, end_date, ad_map, source_map)
        _refresh_conversion_data(start_date, end_date)
        statsd_incr('reports.refresh_demo_data_successful')
    except:
        logger.exception('Refreshing demo data failed')
        statsd_incr('reports.refresh_demo_data_failed')


def _copy_content_ads():
    ad_map, source_map = {}, {}
    
    ads_copied = 0
    
    for demo_ad_group in dash.models.AdGroup.demo_objects.all():
        demo2real = dash.models.DemoAdGroupRealAdGroup.objects.get(
            demo_ad_group=demo_ad_group
        )

        real_ad_group = demo2real.real_ad_group

        real_sources_ids = {
            source.id : source for source in
            dash.models.ContentAdSource.objects.filter(content_ad__ad_group=real_ad_group)
        }
        demo_sources = dash.models.ContentAdSource.objects.filter(content_ad__ad_group=demo_ad_group)
        
        if demo_sources:
            try:
                for source in demo_sources:
                    real_source_id = int(source.source_content_ad_id)
                    ad_map[real_sources_ids[real_source_id].content_ad_id] = source.content_ad_id
                    source_map[real_source_id] = source.id
                logger.info('Ads were already copied - rebuilt ad and source map to real ad groups and sources')
                continue
            except:
                # We are working with an ad group where demo data
                # hasn't migrated to the new version yet
                reports.models.ContentAdStats.objects.filter(
                    content_ad__ad_group=demo_ad_group
                ).delete()
                demo_sources.delete()
                dash.models.ContentAd.objects.filter(
                    ad_group=demo_ad_group
                ).delete()
                logger.info('Ads and sources don\'t exists, clearing state and copying ads ... ')
    
        for i, ad in enumerate(dash.models.ContentAd.objects.filter(ad_group=real_ad_group)):
            real_ad_id = ad.id

            batch = ad.batch
            batch.pk = None
            batch.brand_name = 'Example.com'
            batch.display_url = 'example.com'
            batch.description = ''
            batch.save()

            ad.pk = None
            ad.ad_group = demo_ad_group
            ad.url = 'http://www.example.com/{}/{}'.format(slugify(ad.title), i)
            ad.batch_id = batch.id
            ad.save()

            ad_map[real_ad_id] = ad.id
    
            for source in dash.models.ContentAdSource.objects.filter(content_ad_id=real_ad_id):
                real_source_id = source.id

                source.pk = None
                source.content_ad = ad
                source.source_content_ad_id = str(real_source_id)
                source.save()
                source_map[real_source_id] = source.id

            ads_copied += 1
    logger.info('Ads copied: %d', ads_copied)
    return ad_map, source_map


def _copy_content_ad_stats(dt, real_ad_group, multiplication_factor, ad_map, source_map):
    stats_copied = 0
    for content_ad in dash.models.ContentAd.objects.filter(ad_group=real_ad_group):
        qs = reports.models.ContentAdStats.objects.filter(
            date=dt,
            content_ad=content_ad
        )

        for row in qs:
            if not _can_demo_stats(row.source):
                continue
            d_row = {
                'date': dt,
                'content_ad_source_id': source_map[row.content_ad_source.id],
                'content_ad_id': ad_map[row.content_ad.id],
                'source': row.source,
            }
            for metric in list(TRAFFIC_METRICS):
                val = getattr(row, metric)
                if val is not None:
                    val *= multiplication_factor  # all business growth occurs here
                    d_row[metric] = val

            reports.models.ContentAdStats.objects.filter(
                date=dt,
                content_ad_source_id=source_map[row.content_ad_source.id],
            ).delete()
            reports.models.ContentAdStats.objects.create(**d_row)
            stats_copied += 1

    logger.info('Stats copied: %d', stats_copied)

            
def _refresh_stats_data(start_date, end_date, ad_map, source_map):
    daterange = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)
    for dt in daterange:
        for demo_ad_group in dash.models.AdGroup.demo_objects.all():
            demo2real = dash.models.DemoAdGroupRealAdGroup.objects.get(
                demo_ad_group=demo_ad_group
            )

            real_ad_group = demo2real.real_ad_group
            multiplication_factor = demo2real.multiplication_factor

            # ARTICLES
            qs = reports.models.ArticleStats.objects.filter(
                datetime=dt,
                ad_group=real_ad_group
            )
            
            demo_rows = []
            for row in qs:
                if not _can_demo_stats(row.source):
                    continue
                d_row = {
                    'article': row.article,
                    'source': row.source
                }
                for metric in list(TRAFFIC_METRICS) + list(POSTCLICK_METRICS):
                    val = getattr(row, metric)
                    if val is not None:
                        val *= multiplication_factor  # all business growth occurs here
                    d_row[metric] = val
                demo_rows.append(d_row)

            reports.update.stats_update_adgroup_all(dt, demo_ad_group, demo_rows)

            # CONTENT ADS
            _copy_content_ad_stats(dt, real_ad_group, multiplication_factor, ad_map, source_map)


def _refresh_conversion_data(start_date, end_date):
    daterange = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)

    for dt in daterange:
        for demo_ad_group in dash.models.AdGroup.demo_objects.all():
            demo2real = dash.models.DemoAdGroupRealAdGroup.objects.get(
                demo_ad_group=demo_ad_group
            )

            real_ad_group = demo2real.real_ad_group
            multiplication_factor = demo2real.multiplication_factor

            qs = reports.models.GoalConversionStats.objects.filter(
                datetime=dt,
                ad_group=real_ad_group
            )

            demo_rows = []
            for row in qs:
                if not _can_demo_stats(row.source):
                    continue
                d_row = {
                    'article': row.article,
                    'source': row.source,
                    'goal_name': row.goal_name,
                }
                for metric in CONVERSION_METRICS:
                    val = getattr(row, metric)
                    if val is not None:
                        val *= multiplication_factor
                    d_row[metric] = val
                demo_rows.append(d_row)

            reports.update.goals_update_adgroup(dt, demo_ad_group, demo_rows)


def _can_demo_stats(source):
    return not source.deprecated
