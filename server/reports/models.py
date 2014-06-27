from django.db import models


class Article(models.Model):

    url = models.CharField(max_length=2048, editable=False, null=True)
    title = models.CharField(max_length=256, editable=False, null=True)

    ad_group = models.ForeignKey('dash.AdGroup')

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')


class ArticleStats(models.Model):

    datetime = models.DateTimeField()

    ad_group = models.ForeignKey('dash.AdGroup')
    article = models.ForeignKey('Article')
    network = models.ForeignKey('dash.Network')

    impressions = models.IntegerField(default=0, blank=False, null=False)
    clicks = models.IntegerField(default=0, blank=False, null=False)
    cpc = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=4,
        blank=False,
        null=False
    )
    cost = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=4,
        blank=False,
        null=False
    )
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at')

    class Meta:

        unique_together = ('datetime', 'ad_group', 'article', 'network')
