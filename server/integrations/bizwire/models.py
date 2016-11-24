import jsonfield
from django.db import models


class AdGroupTargeting(models.Model):

    ad_group = models.ForeignKey('dash.AdGroup')
    interest_targeting = jsonfield.JSONField(default=[])
    start_date = models.DateField()

    class Meta:
        unique_together = ('start_date', 'interest_targeting')
