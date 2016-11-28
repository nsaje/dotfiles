import jsonfield
from django.db import models


class AdGroupTargeting(models.Model):

    ad_group = models.ForeignKey('dash.AdGroup')
    interest_targeting = jsonfield.JSONField(default=[])
    start_date = models.DateField()

    def __repr__(self):
        return 'AdGroupTargeting: [{} - {}: {}]'.format(
            self.start_date.isoformat(), self.interest_targeting, self.ad_group_id)

    class Meta:
        unique_together = ('start_date', 'interest_targeting')
