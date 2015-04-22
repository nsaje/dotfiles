import copy
import logging

from django.db import transaction

import reports.api
import reports.refresh
import reports.models
import dash.models

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
            'Deleting stats for ad group: %s, source: %s, datetime: %s; clicks: %s, '
            'impressions: %s, cost_cc: %s, data_cost_cc: %s, avg has_traffic_metrics: %s',
            ad_group,
            source,
            datetime,
            sum(stat.clicks for stat in stats),
            sum(stat.impressions for stat in stats),
            sum(stat.cost_cc for stat in stats),
            sum(stat.data_cost_cc for stat in stats),
            sum(stat.data.has_traffic_metrics for stat in stats) / len(stats),
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

    content_ad_sources = {}
    for content_ad_source in dash.models.ContentAdSource.objects.filter(
            content_ad__ad_group=ad_group, source=source):
        content_ad_sources[content_ad_source.get_source_id()] = content_ad_source

    for row in rows:
        content_ad_source = content_ad_sources.get(row['id'])

        if content_ad_source is None:
            logger.info(
                'Ignoring content ad data with unknown id: {} for ad group id: {} source id: {}, date: {}',
                row['id'], ad_group.id, source.id, date)
            continue

        reports.models.ContentAdStats.objects.create(
            date=date,
            content_ad_source=content_ad_source,
            content_ad=content_ad_source.content_ad,
            source=content_ad_source.source,
            impressions=row['impressions'],
            clicks=row['clicks'],
            cost_cc=row['cost_cc'],
            data_cost_cc=row['data_cost_cc'],
        )
