from django.db import models


class AdGroupRotation(models.Model):

    ad_group = models.ForeignKey("dash.AdGroup")
    start_date = models.DateField(unique=True)

    def __repr__(self):
        return "AdGroupRotation: [{}: {}]".format(self.start_date.isoformat(), self.ad_group_id)
