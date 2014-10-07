import copy

from django.db import transaction

from reports.models import TRAFFIC_METRICS, POSTCLICK_METRICS, CONVERSION_METRICS, ArticleStats, GoalConversionStats

import reports.refresh
import reports.models


class StatsUpdater(object):

    @transaction.atomic
    def update_adgroup_source_traffic(self, datetime, ad_group, source, rows):
        '''
        rows is a list of dictionaries of the form:
        [{article:<dash.Article obj>, impressions:<int>, clicks:<int>, cost_cc:<int>}, ...]

        *Note*: rows contains all traffic data for the given datetime, ad_group and source
        '''
        # reset traffic metrics
        for article_stats in ArticleStats.objects.filter(datetime=datetime, ad_group=ad_group, source=source):
            article_stats.reset_traffic_metrics()

        # save the data
        for row in rows:
            dimensions = dict(
                datetime=datetime,
                article=row['article'],
                ad_group=ad_group,
                source=source
            )
            try:
                article_stats = ArticleStats.objects.get(**dimensions)
                for metric, value in row.items():
                    if metric in TRAFFIC_METRICS:
                        article_stats.__setattr__(metric, article_stats.__getattribute__(metric) + value)
            except ArticleStats.DoesNotExist:
                fields = copy.copy(dimensions)
                fields.update(row)
                article_stats = ArticleStats(**fields)

            article_stats.has_traffic_metrics = 1
            article_stats.save()

        # refresh the corresponding adgroup-level pre-aggregations
        reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group, source=source)

    @transaction.atomic
    def update_adgroup_postclick(self, datetime, ad_group, rows):
        '''
        rows is a list of dictionaries of the form
        [{
            article:<dash.Article obj>, source:<dash.Source obj>,
            visits:<int>, new_visits:<int>, bounced_visits:<int>,
            pageviews:<int>, duration:<int>
        }, ... ]

        *Note*: rows contains all postclick data for the given datetime and ad_group
        '''
        # reset postclick metrics
        for article_stats in ArticleStats.objects.filter(datetime=datetime, ad_group=ad_group):
            article_stats.reset_postclick_metrics()

        # save the data
        for row in rows:
            dimensions=dict(
                datetime=datetime,
                article=row['article'],
                ad_group=ad_group,
                source=row['source']
            )
            try:
                article_stats = ArticleStats.objects.get(**dimensions)
                for metric, value in row.items():
                    if metric in POSTCLICK_METRICS:
                        article_stats.__setattr__(metric, article_stats.__getattribute__(metric) + value)
            except ArticleStats.DoesNotExist:
                fields = copy.copy(dimensions)
                fields.update(row)
                article_stats = ArticleStats(**fields)

            article_stats.has_postclick_metrics = 1
            article_stats.save()

        # refresh the corresponding adgroup-level pre-aggregations
        reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)


class ConversionsUpdater(object):

    @transaction.atomic
    def update_adgroup(self, datetime, ad_group, rows):
        '''
        rows is a list of dictionaries of the form
        [{
            article:<dash.Article obj>, source:<dash.Source obj>, goal_name:<str>,
            conversions:<int>, conversions_value_cc:<int>
        }, ... ]

        *Note*: rows contains all conversion data for the given datetime and ad_group
        '''
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
                        conv_stats.__setattr__(metric, conv_stats.__getattribute__(metric) + value)
            except GoalConversionStats.DoesNotExist:
                fields = copy.copy(dimensions)
                fields.update(row)
                conv_stats = GoalConversionStats(**fields)
            conv_stats.save()

        # refresh the corresponding adgroup-level pre-aggregations
        reports.refresh.refresh_adgroup_stats(datetime=datetime, ad_group=ad_group)
        reports.refresh.refresh_adgroup_conversion_stats(datetime=datetime, ad_group=ad_group)
