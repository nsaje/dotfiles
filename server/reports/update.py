import copy
import logging

from django.db import transaction

from reports.models import TRAFFIC_METRICS, POSTCLICK_METRICS, CONVERSION_METRICS, ArticleStats, GoalConversionStats

import reports.refresh
import reports.models

logger = logging.getLogger(__name__)

@transaction.atomic
def stats_update_adgroup_source_traffic(datetime, ad_group, source, rows):
    '''
    rows is a list of dictionaries of the form:
    [{article:<dash.Article obj>, impressions:<int>, clicks:<int>, cost_cc:<int>}, ...]

    *Note*: rows contains all traffic data for the given datetime, ad_group and source
    '''

    if len(rows) == 0:
        logger.warning('Update of source traffic for adgroup %d, source %d, datetime %s skipped, due to empty rows.',
                       ad_group.id, source.id, datetime)
        return

    stats = ArticleStats.objects.filter(
        datetime=datetime, ad_group=ad_group, source=source
    ).select_related('article')

    # bulk update to reset traffic metrics
    stats.update(
        impressions=0,
        clicks=0,
        cost_cc=0,
        data_cost_cc=None
    )

    stats_dict = {stat.article.id: stat for stat in stats}

    aggregated_stats = {}
    max_has_postclick_metrics = 0
    max_has_conversion_metrics = 0

    for row in rows:
        # update the stats aggregate
        for key, val in row.iteritems():
            if key not in TRAFFIC_METRICS:
                continue
            if key not in aggregated_stats:
                aggregated_stats[key] = 0
            aggregated_stats[key] += val

        article_stats = stats_dict.get(row['article'].id)

        if article_stats is None:
            fields = dict(
                datetime=datetime,
                article=row['article'],
                ad_group=ad_group,
                source=source
            )
            fields.update(row)

            article_stats = ArticleStats(**fields)

            # update stats dict with newly created ArticleStats object
            stats_dict[article_stats.article.id] = article_stats
        else:
            if article_stats.has_postclick_metrics == 1:
                max_has_postclick_metrics = 1
            if article_stats.has_conversion_metrics == 1:
                max_has_conversion_metrics = 1
            for metric, value in row.items():
                if metric in TRAFFIC_METRICS:
                    setattr(article_stats, metric, getattr(article_stats, metric) + value)

        article_stats.has_traffic_metrics = 1
        article_stats.save()

    # update the corresponding adgroup-level pre-aggregations
    fields = dict(
        datetime=datetime,
        ad_group=ad_group,
        source=source
    )

    try:
        adgroup_stats = reports.models.AdGroupStats.objects.get(**fields)
        # we don't call this refresh function on purpose,
        # because we don't actually need to query the db to compute the aggregates,
        # and it is cheaper to just compute the aggregate_stats as we update the article stats
        for metric, value in aggregated_stats.items():
            setattr(adgroup_stats, metric, value)
    except reports.models.AdGroupStats.DoesNotExist:
        fields.update(aggregated_stats)
        adgroup_stats = reports.models.AdGroupStats(**fields)

    adgroup_stats.has_traffic_metrics = 1
    adgroup_stats.has_postclick_metrics = max_has_postclick_metrics
    adgroup_stats.has_conversion_metrics = max_has_conversion_metrics
    adgroup_stats.save()


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
    for article_stats in ArticleStats.objects.filter(datetime=datetime, ad_group=ad_group):
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
            article_stats = ArticleStats.objects.get(**dimensions)
            for metric, value in row.items():
                if metric in POSTCLICK_METRICS:
                    setattr(article_stats, metric, getattr(article_stats, metric) + value)
        except ArticleStats.DoesNotExist:
            fields = copy.copy(dimensions)
            fields.update(row)
            article_stats = ArticleStats(**fields)

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
    for article_stats in ArticleStats.objects.filter(datetime=datetime, ad_group=ad_group):
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
            article_stats = ArticleStats.objects.get(**dimensions)
            for metric, value in row.items():
                if metric in TRAFFIC_METRICS or metric in POSTCLICK_METRICS:
                    setattr(article_stats, metric, getattr(article_stats, metric) + value)
        except ArticleStats.DoesNotExist:
            fields = copy.copy(dimensions)
            fields.update(row)
            article_stats = ArticleStats(**fields)

        article_stats.has_traffic_metrics = 1
        article_stats.has_postclick_metrics = 1
        article_stats.save()

    # refresh the corresponding adgroup-level pre-aggregations
    reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)


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
    for conv_stats in GoalConversionStats.objects.filter(datetime=datetime, ad_group=ad_group):
        conv_stats.reset_metrics()

    for row in rows:
        # set has_conversion_metrics flag in ArticleStats
        try:
            article_stats = ArticleStats.objects.get(
                datetime=datetime, article=row['article'],
                ad_group=ad_group, source=row['source'])
        except ArticleStats.DoesNotExist:
            article_stats = ArticleStats(datetime=datetime,
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
            conv_stats = GoalConversionStats.objects.get(**dimensions)
            for metric, value in row.items():
                if metric in CONVERSION_METRICS:
                    setattr(conv_stats, metric, getattr(conv_stats, metric) + value)
        except GoalConversionStats.DoesNotExist:
            fields = copy.copy(dimensions)
            fields.update(row)
            conv_stats = GoalConversionStats(**fields)
        conv_stats.save()

    # refresh the corresponding adgroup-level pre-aggregations
    reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)
    reports.refresh.refresh_adgroup_conversion_stats(datetime=datetime, ad_group=ad_group)
