from django.db import models


class ArticleStats(models.Model):

    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup')
    article = models.ForeignKey('dash.Article')
    network = models.ForeignKey('dash.Network')

    impressions = models.IntegerField(default=0, blank=False, null=False)
    clicks = models.IntegerField(default=0, blank=False, null=False)
    cost_cc = models.IntegerField(default=0, blank=False, null=False)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:

        unique_together = ('datetime', 'ad_group', 'article', 'network')
