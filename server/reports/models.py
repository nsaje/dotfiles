from django.db import models


class ArticleStats(models.Model):

    date = models.DateField()
    ad_group = models.IntegerField()
    article = models.IntegerField()
    network = models.IntegerField()
    impressions = models.IntegerField()
    clicks = models.IntegerField()
    cpc = models.FloatField()
    cost = models.FloatField()

    class Meta:

        unique_together = ('date', 'ad_group', 'article', 'network')



