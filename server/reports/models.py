from django.db import models

TRAFFIC_METRICS = {'impressions', 'clicks', 'cost_cc', 'data_cost_cc'}
POSTCLICK_METRICS = {'visits', 'pageviews', 'new_visits', 'bounced_visits', 'duration'}
CONVERSION_METRICS = {'conversions', 'conversions_value_cc'}

# CAUTION: Do not use these models directly in your code
# For querying use the functions from reports.api
# For inserting/updating data use the functions from reports.update


class StatsMetrics(models.Model):
    # traffic metrics
    impressions = models.IntegerField(default=0, blank=False, null=False)
    clicks = models.IntegerField(default=0, blank=False, null=False)
    cost_cc = models.IntegerField(default=0, blank=False, null=False)
    data_cost_cc = models.IntegerField(default=0, blank=False, null=False)

    # postclick metrics
    visits = models.IntegerField(default=0, blank=False, null=False)
    new_visits = models.IntegerField(default=0, blank=False, null=False)
    bounced_visits = models.IntegerField(default=0, blank=False, null=False)
    pageviews = models.IntegerField(default=0, blank=False, null=False)
    duration = models.IntegerField(default=0, blank=False, null=False)

    has_traffic_metrics = models.IntegerField(default=0, blank=False, null=False)
    has_postclick_metrics = models.IntegerField(default=0, blank=False, null=False)
    has_conversion_metrics = models.IntegerField(default=0, blank=False, null=False)

    class Meta:
        abstract = True


class ArticleStats(StatsMetrics):

    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup', on_delete=models.PROTECT)
    article = models.ForeignKey('dash.Article', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        unique_together = (
            ('datetime', 'ad_group', 'article', 'source'),
        )

        index_together = (['ad_group', 'datetime'])

        permissions = (
            ("yesterday_spend_view", "Can view yesterday spend column."),
            ("per_day_sheet_source_export", "Has Per-Day Report sheet in Excel source export.")
        )

    def reset_traffic_metrics(self):
        self.impressions = 0
        self.clicks = 0
        self.cost_cc = 0
        self.data_cost_cc = 0
        self.has_traffic_metrics = 0
        self.save()

    def reset_postclick_metrics(self):
        self.visits = 0
        self.new_visits = 0
        self.bounced_visits = 0
        self.pageviews = 0
        self.duration = 0
        self.has_postclick_metrics = 0
        self.save()


class GoalConversionStats(models.Model):

    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup', on_delete=models.PROTECT)
    article = models.ForeignKey('dash.Article', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    goal_name = models.CharField(max_length=127, blank=False, null=False)

    # conversion metrics
    conversions = models.IntegerField(default=0, blank=False, null=False)
    conversions_value_cc = models.IntegerField(default=0, blank=False, null=False)

    class Meta:
        unique_together = (
            ('datetime', 'ad_group', 'article', 'source', 'goal_name'),
        )

    def reset_metrics(self):
        self.conversions = 0
        self.conversions_value_cc = 0
        self.save()


# The following models are preaggregated for better querying performance

class AdGroupStats(StatsMetrics):

    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        unique_together = (
            ('datetime', 'ad_group', 'source'),
        )


class AdGroupGoalConversionStats(models.Model):
    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    goal_name = models.CharField(max_length=127, blank=False, null=False)

    # conversion metrics
    conversions = models.IntegerField(default=0, blank=False, null=False)
    conversions_value_cc = models.IntegerField(default=0, blank=False, null=False)

    class Meta:
        unique_together = (
            ('datetime', 'ad_group', 'source', 'goal_name'),
        )


class ContentAdStats(models.Model):
    impressions = models.IntegerField(null=True)
    clicks = models.IntegerField(null=True)
    cost_cc = models.IntegerField(null=True)
    data_cost_cc = models.IntegerField(null=True)

    date = models.DateField()
    content_ad_source = models.ForeignKey('dash.ContentAdSource', on_delete=models.PROTECT)

    # these two foreign keys are added to reduce joins
    content_ad = models.ForeignKey('dash.ContentAd', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        unique_together = (
            ('date', 'content_ad_source'),
        )


class SupplyReportRecipient(models.Model):
    first_name = models.CharField('first name', max_length=30, blank=True)
    last_name = models.CharField('last name', max_length=30, blank=True)
    email = models.EmailField('email address', max_length=255, unique=True)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(auto_now=True, verbose_name='Modified at')


class ContentAdPostclickStats(models.Model):
    date = models.DateTimeField(auto_now_add=False, verbose_name='Report date')
    content_ad = models.ForeignKey('dash.ContentAd', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    visits = models.IntegerField(default=0, blank=False, null=False)
    new_visits = models.IntegerField(default=0, blank=False, null=False)
    bounced_visits = models.IntegerField(default=0, blank=False, null=False)
    pageviews = models.IntegerField(default=0, blank=False, null=False)
    total_time_on_site = models.IntegerField(default=0, blank=False, null=False)

    class Meta:
        unique_together = (
            ('date', 'content_ad', 'source'),
        )


class ContentAdGoalConversionStats(models.Model):
    date = models.DateTimeField(auto_now_add=False, verbose_name='Report date')
    content_ad = models.ForeignKey('dash.ContentAd', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    goal_type = models.CharField(max_length=256, editable=False, null=False)
    goal_name = models.CharField(max_length=256, editable=False, null=False)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    conversions = models.CharField(max_length=256, editable=False, null=False)

    class Meta:
        unique_together = (
            ('date', 'content_ad', 'source', 'goal_type', 'goal_name'),
        )
