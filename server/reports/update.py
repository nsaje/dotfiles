import copy
import datetime
import logging

from django.db import transaction
from django.conf import settings

import dash.models

import reports.api
import reports.refresh
import reports.models
from reports import refresh
from reports import redshift
from utils.statsd_helper import statsd_timer

from utils import statsd_helper

logger = logging.getLogger(__name__)


@transaction.atomic
def stats_update_adgroup_source_traffic(datetime, ad_group, source, rows):
    '''
    rows is a list of dictionaries of the form:
    [{article:<dash.Article obj>, impressions:<int>, clicks:<int>, cost_cc:<int>, [data_cost_cc:<int>]}, ...]

    *Note*: rows contains all traffic data for the given datetime, ad_group and source
    '''
    if len(rows) == 0 and not reports.api.can_delete_traffic_metrics(ad_group, source, datetime):
        return

    stats = reports.models.ArticleStats.objects.filter(
        datetime=datetime, ad_group=ad_group, source=source
    ).select_related('article')

    if len(rows) == 0 and stats.count() > 0:
        logger.warning(
            'Deleting stats for ad group id: %d, source id: %d, datetime: %s; clicks: %s, '
            'impressions: %s, cost_cc: %s, data_cost_cc: %s, avg has_traffic_metrics: %s',
            ad_group.id,
            source.id,
            datetime,
            sum(stat.clicks for stat in stats),
            sum(stat.impressions for stat in stats),
            sum(stat.cost_cc for stat in stats),
            sum(stat.data_cost_cc for stat in stats),
            sum(stat.has_traffic_metrics for stat in stats) / len(stats),
        )

    stats.update(
        impressions=0,
        clicks=0,
        cost_cc=0,
        data_cost_cc=0,
        has_traffic_metrics=0,
    )

    stats_dict = {stat.article.id: stat for stat in stats}
    for row in rows:
        article_stats = stats_dict.get(row['article'].id)

        if article_stats is None:
            fields = dict(
                datetime=datetime,
                article=row['article'],
                ad_group=ad_group,
                source=source
            )
            fields.update(row)

            article_stats = reports.models.ArticleStats(**fields)

            # update stats dict with newly created ArticleStats object
            stats_dict[article_stats.article.id] = article_stats
        else:
            for metric, value in row.items():
                if metric in reports.models.TRAFFIC_METRICS:
                    setattr(article_stats, metric, getattr(article_stats, metric) + value)

        article_stats.has_traffic_metrics = 1
        article_stats.save()

    reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group, source=source)


@statsd_helper.statsd_timer('reports', 'stats_update_adgroup_postclick')
@transaction.atomic
def stats_update_adgroup_postclick(datetime, ad_group, rows):
    '''
    rows is a list of dictionaries of the form
    [{
        article:<dash.Article obj>, source:<dash.Source obj>,
        visits:<int>, new_visits:<int>, bounced_visits:<int>,
        pageviews:<int>, duration:<int>
    }, ... ]

    *Note*: rows contains all postclick data for the given datetime and ad_group
    '''

    if len(rows) == 0:
        logger.warning('Update of adgroup postclick for adgroup %d, datetime %s skipped, due to empty rows.',
                       ad_group.id, datetime)
        return

    # reset postclick metrics
    for article_stats in reports.models.ArticleStats.objects.filter(datetime=datetime, ad_group=ad_group):
        article_stats.reset_postclick_metrics()

    # save the data
    for row in rows:
        dimensions = dict(
            datetime=datetime,
            article=row['article'],
            ad_group=ad_group,
            source=row['source']
        )
        try:
            article_stats = reports.models.ArticleStats.objects.get(**dimensions)
            for metric, value in row.items():
                if metric in reports.models.POSTCLICK_METRICS:
                    setattr(article_stats, metric, getattr(article_stats, metric) + value)
        except reports.models.ArticleStats.DoesNotExist:
            fields = copy.copy(dimensions)
            fields.update(row)
            article_stats = reports.models.ArticleStats(**fields)

        article_stats.has_postclick_metrics = 1
        article_stats.save()

    # refresh the corresponding adgroup-level pre-aggregations
    reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)


def stats_update_adgroup_all(datetime, ad_group, rows):
    '''
    rows is a list of dictionaries of the form
    [{
        article:<dash.Article obj>, source:<dash.Source obj>,
        impressions:<int>, clicks:<int>, cost_cc:<int>,
        visits:<int>, new_visits:<int>, bounced_visits:<int>,
        pageviews:<int>, duration:<int>
    }, ... ]

    *Note*: rows contains all traffic and postclick data for the given datetime and ad_group
    '''

    if len(rows) == 0:
        logger.warning('Update of adgroup all stats for adgroup %d, datetime %s skipped, due to empty rows.',
                       ad_group.id, datetime)
        return

    # reset metrics
    for article_stats in reports.models.ArticleStats.objects.filter(datetime=datetime, ad_group=ad_group):
        article_stats.reset_traffic_metrics()
        article_stats.reset_postclick_metrics()

    # save the data
    for row in rows:
        dimensions = dict(
            datetime=datetime,
            article=row['article'],
            ad_group=ad_group,
            source=row['source']
        )
        try:
            article_stats = reports.models.ArticleStats.objects.get(**dimensions)
            for metric, value in row.items():
                if metric in reports.models.TRAFFIC_METRICS or metric in reports.models.POSTCLICK_METRICS:
                    setattr(article_stats, metric, getattr(article_stats, metric) + value)
        except reports.models.ArticleStats.DoesNotExist:
            fields = copy.copy(dimensions)
            fields.update(row)
            article_stats = reports.models.ArticleStats(**fields)

        article_stats.has_traffic_metrics = 1
        article_stats.has_postclick_metrics = 1
        article_stats.save()

    # refresh the corresponding adgroup-level pre-aggregations
    reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)


@statsd_helper.statsd_timer('reports', 'goals_update_adgroup')
@transaction.atomic
def goals_update_adgroup(datetime, ad_group, rows):
    '''
    rows is a list of dictionaries of the form
    [{
        article:<dash.Article obj>, source:<dash.Source obj>, goal_name:<str>,
        conversions:<int>, conversions_value_cc:<int>
    }, ... ]

    *Note*: rows contains all conversion data for the given datetime and ad_group
    '''

    if len(rows) == 0:
        logger.warning('Update of adgroup goals for adgroup %d, datetime %s skipped, due to empty rows.',
                       ad_group.id, datetime)
        return

    # reset conversion metrics
    for conv_stats in reports.models.GoalConversionStats.objects.filter(datetime=datetime, ad_group=ad_group):
        conv_stats.reset_metrics()

    for row in rows:
        # set has_conversion_metrics flag in ArticleStats
        try:
            article_stats = reports.models.ArticleStats.objects.get(
                datetime=datetime, article=row['article'],
                ad_group=ad_group, source=row['source'])
        except reports.models.ArticleStats.DoesNotExist:
            article_stats = reports.models.ArticleStats(
                datetime=datetime,
                article=row['article'], ad_group=ad_group,
                source=row['source'])
        article_stats.has_conversion_metrics = 1
        article_stats.save()

        # save conversion data
        dimensions = dict(
            datetime=datetime,
            ad_group=ad_group,
            article=row['article'],
            source=row['source'],
            goal_name=row['goal_name'],
        )
        try:
            conv_stats = reports.models.GoalConversionStats.objects.get(**dimensions)
            for metric, value in row.items():
                if metric in reports.models.CONVERSION_METRICS:
                    setattr(conv_stats, metric, getattr(conv_stats, metric) + value)
        except reports.models.GoalConversionStats.DoesNotExist:
            fields = copy.copy(dimensions)
            fields.update(row)
            conv_stats = reports.models.GoalConversionStats(**fields)
        conv_stats.save()

    # refresh the corresponding adgroup-level pre-aggregations
    reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)
    reports.refresh.refresh_adgroup_conversion_stats(datetime=datetime, ad_group=ad_group)


@transaction.atomic
def update_content_ads_source_traffic_stats(date, ad_group, source, rows):
    if len(rows) == 0 and not reports.api.can_delete_traffic_metrics(ad_group, source, date):
        return

    reports.models.ContentAdStats.objects.filter(
        date=date,
        content_ad_source__content_ad__ad_group=ad_group,
        source=source,
    ).delete()

    for row in rows:
        if 'content_ad_source' not in row:
            statsd_helper.statsd_incr('reports.update.err_missing_content_ad_data')
            raise Exception('missing content ad data')

        content_ad_source = row['content_ad_source']
        reports.models.ContentAdStats.objects.create(
            date=date,
            content_ad_source=content_ad_source,
            content_ad=content_ad_source.content_ad,
            source=content_ad_source.source,
            impressions=row['impressions'],
            clicks=row['clicks'],
            cost_cc=row['cost_cc'],
            data_cost_cc=row.get('data_cost_cc'),
        )

    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()


@transaction.atomic(using=settings.STATS_DB_NAME)
def update_touchpoint_conversions(date, account_id, slug, conversion_touchpoint_pairs):
    redshift.delete_touchpoint_conversions(date, account_id, slug)
    redshift.insert_touchpoint_conversions(conversion_touchpoint_pairs)


@statsd_timer('reports.update', 'process_report')
@transaction.atomic
def process_report(date, parsed_report_rows, report_type):
    """
    Stores postclick stats and conversion goals stats
    to DB and updates stats DB
    """
    try:
        sources = dash.models.Source.objects.all()
        track_source_map = {}
        for source in sources:
            track_source_map[source.tracking_slug] = source.id

        bulk_contentad_stats = []
        bulk_goal_conversion_stats = []
        content_ad_ids = set()
        for entry in parsed_report_rows:
            content_ad_ids.add(entry.content_ad_id)

            stats = _create_contentad_postclick_stats(entry, track_source_map)
            if stats is None:
                continue
            bulk_contentad_stats.append(stats)

            goal_conversion_stats = _create_contentad_goal_conversion_stats(entry, report_type, track_source_map)
            bulk_goal_conversion_stats.extend(goal_conversion_stats)

        _delete_and_restore_bulk_stats(report_type, bulk_contentad_stats, bulk_goal_conversion_stats)
    except:
        logger.exception('Failed processing report')
        raise


@statsd_timer('reports.update', '_delete_and_restore_bulk_stats')
def _delete_and_restore_bulk_stats(report_type, bulk_contentad_stats, bulk_goal_conversion_stats):
    for obj in bulk_contentad_stats:
        reports.models.ContentAdPostclickStats.objects.filter(
            date=obj.date,
            content_ad__id=obj.content_ad_id,
            source__id=obj.source_id
        ).delete()

    for obj in bulk_goal_conversion_stats:
        reports.models.ContentAdGoalConversionStats.objects.filter(
            date=obj.date,
            content_ad__id=obj.content_ad_id,
            source__id=obj.source_id,
            goal_type=report_type,
        ).delete()

    for obj in bulk_contentad_stats:
        obj.save()

    for obj in bulk_goal_conversion_stats:
        obj.save()


def _create_contentad_postclick_stats(entry, track_source_map):
    created_dt = datetime.datetime.utcnow()
    try:
        stats = reports.models.ContentAdPostclickStats(
            date=entry.report_date,
            created_dt=created_dt,
            visits=entry.visits,
            new_visits=entry.new_visits,
            bounced_visits=entry.bounced_visits,
            pageviews=entry.pageviews,
            total_time_on_site=entry.total_time_on_site,
        )
        stats.source_id = track_source_map[entry.source_param]
        stats.content_ad_id = entry.content_ad_id
        return stats
    except:
        logger.exception("Failed parsing content ad {blob}".format(
            blob=entry
        ))
        raise
    return None


def _create_contentad_goal_conversion_stats(entry, goal_type, track_source_map):
    created_dt = datetime.datetime.utcnow()
    try:
        report_date = entry.report_date
        stats = []
        for goal, conversions in entry.goals.iteritems():
            stat = reports.models.ContentAdGoalConversionStats(
                date=report_date,
                created_dt=created_dt,
                goal_type=goal_type,
                goal_name=goal,
                conversions=conversions,
            )
            stat.source_id = track_source_map[entry.source_param]
            stat.content_ad_id = entry.content_ad_id
            stats.append(stat)
        return stats
    except:
        logger.exception("Failed parsing content ad {blob}".format(
            blob=entry
        ))
        raise
    return []
