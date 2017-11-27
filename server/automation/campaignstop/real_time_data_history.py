from django.db import models

import core.entity
import core.source


class RealTimeDataHistory(models.Model):
    class Meta:
        unique_together = ('ad_group', 'source', 'date')

    ad_group = models.ForeignKey(core.entity.AdGroup)
    source = models.ForeignKey(core.source.Source)
    date = models.DateField()
    etfm_spend = models.DecimalField(
        max_digits=14,
        decimal_places=4,
    )
