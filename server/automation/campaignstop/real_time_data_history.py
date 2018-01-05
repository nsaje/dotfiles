from django.db import models

import core.entity
import core.source


class RealTimeDataHistory(models.Model):
    ad_group = models.ForeignKey(core.entity.AdGroup)
    source = models.ForeignKey(core.source.Source)
    date = models.DateField(db_index=True)
    etfm_spend = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at', db_index=True)


class RealTimeCampaignDataHistory(models.Model):
    campaign = models.ForeignKey(core.entity.Campaign)
    date = models.DateField(db_index=True)
    etfm_spend = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
    )

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name='Created at', db_index=True)
