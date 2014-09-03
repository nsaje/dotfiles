from django.db import models


class ArticleStats(models.Model):

    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup', on_delete=models.PROTECT)
    article = models.ForeignKey('dash.Article', on_delete=models.PROTECT)
    source = models.ForeignKey('dash.Source', on_delete=models.PROTECT)

    # traffic metrics
    impressions = models.IntegerField(default=0, blank=False, null=False)
    clicks = models.IntegerField(default=0, blank=False, null=False)
    cost_cc = models.IntegerField(default=0, blank=False, null=False)
    

     # postclick metrics
    visits = models.IntegerField(default=0, blank=False, null=False)
    new_visits = models.IntegerField(default=0, blank=False, null=False)
    bounced_visits = models.IntegerField(default=0, blank=False, null=False)
    pageviews = models.IntegerField(default=0, blank=False, null=False)
    duration = models.IntegerField(default=0, blank=False, null=False)

    has_traffic_metrics = models.IntegerField(default=0, blank=False, null=False)
    has_postclick_metrics = models.IntegerField(default=0, blank=False, null=False)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:
        unique_together = (
            ('datetime', 'ad_group', 'article', 'source'),
        )

        permissions = (
            ("yesterday_spend_view", "Can view yesterday spend column."),
            ("fewer_daterange_options", "Has fewer options available in daterange picker."),
            ("per_day_sheet_source_export", "Has Per-Day Report sheet in Excel source export.")
        )

    def reset_traffic_metrics(self):
        self.impressions = 0
        self.clicks = 0
        self.cost_cc = 0
        self.save()

    def reset_postclick_metrics(self):
        self.visits = 0
        self.new_visits = 0
        self.bounced_visits = 0
        self.pageviews = 0
        self.duration = 0
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

    has_conversion_metrics = models.IntegerField(default=0, blank=False, null=False)

    class Meta:
        unique_together = (
            ('datetime', 'ad_group', 'article', 'source', 'goal_name'),
        )
